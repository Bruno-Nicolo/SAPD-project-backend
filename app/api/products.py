import csv
import io
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.models.schemas import (
    ProductCreate,
    ProductResponse,
    ScoringRequest,
    ScoreResponse,
    BadgeApply,
    ComponentCreate,
)
from app.core.patterns.composite import CompositeProduct, SimpleComponent
from app.core.patterns.strategy import (
    ScoringContext,
    HiggIndexStrategy,
    CarbonFootprintStrategy,
    CircularEconomyStrategy,
)
from app.core.patterns.decorator import (
    FairTradeBadge,
    VeganBadge,
    OekoTexBadge,
    NonCompliantBadge,
)
from app.core.patterns.visitor import (
    PdfReportVisitor,
    ComplianceAuditVisitor,
    SocialReportVisitor,
)
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_optional_user
from app.models.db_models import User, Product, Component

router = APIRouter(prefix="/products", tags=["products"])

# In-memory cache for pattern operations (scoring, badges, visitors)
# This maintains compatibility with the existing pattern implementations
products_cache: dict[int, CompositeProduct] = {}

STRATEGY_MAP = {
    "higg_index": HiggIndexStrategy,
    "carbon_footprint": CarbonFootprintStrategy,
    "circular_economy": CircularEconomyStrategy,
}

BADGE_MAP = {
    "fairtrade": FairTradeBadge,
    "vegan": VeganBadge,
    "oekotex": OekoTexBadge,
    "non_compliant": NonCompliantBadge,
}


def _db_product_to_composite(db_product: Product) -> CompositeProduct:
    """Convert a database Product to a CompositeProduct for pattern operations."""
    composite = CompositeProduct(db_product.name)
    for comp in db_product.components:
        simple = SimpleComponent(
            name=comp.name,
            material=comp.material,
            weight_kg=comp.weight_kg,
            environmental_impact=comp.environmental_impact,
        )
        composite.add(simple)
    return composite


def _get_composite_product(db_product: Product) -> CompositeProduct:
    """Get or create a CompositeProduct from cache."""
    if db_product.id not in products_cache:
        products_cache[db_product.id] = _db_product_to_composite(db_product)
    return products_cache[db_product.id]


@router.post("/", response_model=ProductResponse)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new product (requires authentication)."""
    # Create database product
    db_product = Product(name=product_data.name, user_id=current_user.id)
    db.add(db_product)
    db.flush()  # Get the ID
    
    # Add components
    for comp in product_data.components:
        db_component = Component(
            product_id=db_product.id,
            name=comp.name,
            material=comp.material,
            weight_kg=comp.weight_kg,
            environmental_impact=comp.environmental_impact,
        )
        db.add(db_component)
    
    db.commit()
    db.refresh(db_product)
    
    # Create composite for cache
    composite = _db_product_to_composite(db_product)
    products_cache[db_product.id] = composite
    
    return ProductResponse(
        id=db_product.id,
        name=db_product.name,
        total_impact=composite.get_base_impact_score(),
        components=[
            ComponentCreate(
                name=c.name,
                material=c.material,
                weight_kg=c.weight_kg,
                environmental_impact=c.environmental_impact,
            )
            for c in db_product.components
        ],
    )


@router.get("/", response_model=list[ProductResponse])
def list_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all products for the current user."""
    products = db.query(Product).filter(Product.user_id == current_user.id).all()
    
    result = []
    for db_product in products:
        composite = _get_composite_product(db_product)
        result.append(ProductResponse(
            id=db_product.id,
            name=db_product.name,
            total_impact=composite.get_base_impact_score(),
            components=[
                ComponentCreate(
                    name=c.name,
                    material=c.material,
                    weight_kg=c.weight_kg,
                    environmental_impact=c.environmental_impact,
                )
                for c in db_product.components
            ],
        ))
    return result


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific product by ID."""
    db_product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()
    
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    composite = _get_composite_product(db_product)
    
    return ProductResponse(
        id=db_product.id,
        name=db_product.name,
        total_impact=composite.get_base_impact_score(),
        components=[
            ComponentCreate(
                name=c.name,
                material=c.material,
                weight_kg=c.weight_kg,
                environmental_impact=c.environmental_impact,
            )
            for c in db_product.components
        ],
    )


@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a CSV file to create products.
    
    Expected CSV format:
    product_name,component_name,material,weight_kg,environmental_impact
    
    Products with the same name in the CSV will be grouped together.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    content = await file.read()
    decoded = content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))
    
    # Check required columns
    required_columns = {'product_name', 'component_name', 'material', 'weight_kg', 'environmental_impact'}
    if not required_columns.issubset(set(reader.fieldnames or [])):
        raise HTTPException(
            status_code=400,
            detail=f"CSV must contain columns: {', '.join(required_columns)}"
        )
    
    # Group rows by product name
    products_dict: dict[str, list] = {}
    for row in reader:
        product_name = row['product_name'].strip()
        if product_name not in products_dict:
            products_dict[product_name] = []
        products_dict[product_name].append({
            'name': row['component_name'].strip(),
            'material': row['material'].strip(),
            'weight_kg': float(row['weight_kg']),
            'environmental_impact': float(row['environmental_impact']),
        })
    
    # Create products
    created_products = []
    for product_name, components in products_dict.items():
        db_product = Product(name=product_name, user_id=current_user.id)
        db.add(db_product)
        db.flush()
        
        for comp in components:
            db_component = Component(
                product_id=db_product.id,
                name=comp['name'],
                material=comp['material'],
                weight_kg=comp['weight_kg'],
                environmental_impact=comp['environmental_impact'],
            )
            db.add(db_component)
        
        created_products.append(product_name)
    
    db.commit()
    
    return {
        "message": f"Successfully created {len(created_products)} products",
        "products": created_products
    }


@router.post("/{product_id}/score", response_model=ScoreResponse)
def calculate_score(
    product_id: int,
    scoring_request: ScoringRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculate sustainability score for a product."""
    db_product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()
    
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    if scoring_request.strategy not in STRATEGY_MAP:
        raise HTTPException(status_code=400, detail="Invalid scoring strategy")

    composite = _get_composite_product(db_product)
    strategy = STRATEGY_MAP[scoring_request.strategy]()
    context = ScoringContext(strategy)
    score = context.calculate(composite)

    return ScoreResponse(strategy=scoring_request.strategy, score=score)


@router.post("/{product_id}/badges")
def apply_badge(
    product_id: int,
    badge_request: BadgeApply,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Apply a badge to a product."""
    db_product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()
    
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    if badge_request.badge_type not in BADGE_MAP:
        raise HTTPException(status_code=400, detail="Invalid badge type")

    composite = _get_composite_product(db_product)
    badge_class = BADGE_MAP[badge_request.badge_type]
    decorated_product = badge_class(composite)
    products_cache[db_product.id] = decorated_product

    return {"message": f"Badge '{badge_request.badge_type}' applied successfully"}


@router.get("/{product_id}/report/pdf")
def generate_pdf_report(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a PDF report for a product."""
    db_product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()
    
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    composite = _get_composite_product(db_product)
    visitor = PdfReportVisitor()
    composite.accept(visitor)

    return {"report": visitor.get_report()}


@router.get("/{product_id}/report/compliance")
def generate_compliance_audit(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a compliance audit report for a product."""
    db_product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()
    
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    composite = _get_composite_product(db_product)
    visitor = ComplianceAuditVisitor()
    composite.accept(visitor)

    return visitor.get_audit_report()


@router.get("/{product_id}/report/social")
def generate_social_report(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a social report for a product."""
    db_product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()
    
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    composite = _get_composite_product(db_product)
    visitor = SocialReportVisitor()
    composite.accept(visitor)

    return visitor.get_social_report()
