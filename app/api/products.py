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
    ComponentResponse,
)
from app.core.patterns.composite import CompositeProduct, SimpleComponent
from app.core.patterns.strategy import (
    ScoringContext,
    HiggIndexStrategy,
    CarbonFootprintStrategy,
    CircularEconomyStrategy,
    CustomStrategy,
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
    "custom": CustomStrategy,
}

BADGE_MAP = {
    "fairtrade": FairTradeBadge,
    "vegan": VeganBadge,
    "oekotex": OekoTexBadge,
    "non_compliant": NonCompliantBadge,
}

# Environmental impact per kg for common fashion materials
# Values are approximate CO2 equivalent kg per kg of material
MATERIAL_IMPACT_MAP: dict[str, float] = {
    # Natural fibers
    "cotton": 8.0,
    "organic_cotton": 4.0,
    "linen": 5.5,
    "hemp": 3.5,
    "wool": 12.0,
    "silk": 15.0,
    # Synthetic fibers
    "polyester": 9.5,
    "recycled_polyester": 5.0,
    "nylon": 12.0,
    "acrylic": 11.0,
    "elastane": 10.0,
    # Regenerated fibers
    "viscose": 7.0,
    "lyocell": 4.5,
    "modal": 5.0,
    # Leather and alternatives
    "leather": 17.0,
    "vegan_leather": 8.0,
    "faux_leather": 9.0,
    # Other materials
    "rubber": 6.0,
    "metal": 15.0,
    "plastic": 10.0,
    "recycled_plastic": 5.5,
    "wood": 2.0,
    "bamboo": 3.0,
    "glass": 8.5,
}

# Default impact for unknown materials
DEFAULT_MATERIAL_IMPACT = 10.0


def get_material_impact(material: str) -> float:
    """Get environmental impact score for a material.
    
    Looks up the material in the impact map (case-insensitive, with underscores for spaces).
    Returns a default value if the material is not found.
    """
    normalized = material.lower().strip().replace(" ", "_").replace("-", "_")
    return MATERIAL_IMPACT_MAP.get(normalized, DEFAULT_MATERIAL_IMPACT)


def _db_product_to_composite(db_product: Product) -> CompositeProduct:
    """Convert a database Product to a CompositeProduct for pattern operations."""
    composite = CompositeProduct(db_product.name)
    for comp in db_product.components:
        simple = SimpleComponent(
            name=comp.name,
            material=comp.material,
            weight_kg=comp.weight_kg,
            environmental_impact=comp.environmental_impact,
            energy_consumption_mj=comp.energy_consumption_mj,
            water_usage_liters=comp.water_usage_liters,
            waste_generation_kg=comp.waste_generation_kg,
            recyclability_score=comp.recyclability_score,
            recycled_content_percentage=comp.recycled_content_percentage,
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
    
    # Add components with calculated environmental impact
    for comp in product_data.components:
        environmental_impact = get_material_impact(comp.material)
        db_component = Component(
            product_id=db_product.id,
            name=comp.name,
            material=comp.material,
            weight_kg=comp.weight_kg,
            environmental_impact=environmental_impact,
            energy_consumption_mj=comp.energy_consumption_mj or 0.0,
            water_usage_liters=comp.water_usage_liters or 0.0,
            waste_generation_kg=comp.waste_generation_kg or 0.0,
            recyclability_score=comp.recyclability_score or 0.0,
            recycled_content_percentage=comp.recycled_content_percentage or 0.0,
        )
        db.add(db_component)
    
    db.commit()
    db.refresh(db_product)
    
    # Create composite for cache
    composite = _db_product_to_composite(db_product)
    products_cache[db_product.id] = composite
    
    # Calculate Average Score
    higg_score = ScoringContext(HiggIndexStrategy()).calculate(composite)
    carbon_score = ScoringContext(CarbonFootprintStrategy()).calculate(composite)
    circular_score = ScoringContext(CircularEconomyStrategy()).calculate(composite)
    
    average_score = round((higg_score + carbon_score + circular_score) / 3.0, 1)
    db_product.average_score = average_score
    db.commit()
    db.refresh(db_product)
    
    return ProductResponse(
        id=db_product.id,
        name=db_product.name,
        average_score=average_score,
        components=[
            ComponentResponse(
                name=c.name,
                material=c.material,
                weight_kg=c.weight_kg,
                environmental_impact=c.environmental_impact,
                energy_consumption_mj=c.energy_consumption_mj,
                water_usage_liters=c.water_usage_liters,
                waste_generation_kg=c.waste_generation_kg,
                recyclability_score=c.recyclability_score,
                recycled_content_percentage=c.recycled_content_percentage,
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
            average_score=db_product.average_score,
            components=[
                ComponentResponse(
                    name=c.name,
                    material=c.material,
                    weight_kg=c.weight_kg,
                    environmental_impact=c.environmental_impact,
                    energy_consumption_mj=c.energy_consumption_mj,
                    water_usage_liters=c.water_usage_liters,
                    waste_generation_kg=c.waste_generation_kg,
                    recyclability_score=c.recyclability_score,
                    recycled_content_percentage=c.recycled_content_percentage,
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
        average_score=db_product.average_score,
        components=[
            ComponentResponse(
                name=c.name,
                material=c.material,
                weight_kg=c.weight_kg,
                environmental_impact=c.environmental_impact,
                energy_consumption_mj=c.energy_consumption_mj,
                water_usage_liters=c.water_usage_liters,
                waste_generation_kg=c.waste_generation_kg,
                recyclability_score=c.recyclability_score,
                recycled_content_percentage=c.recycled_content_percentage,
            )
            for c in db_product.components
        ],
    )


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a specific product by ID."""
    db_product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()
    
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Remove from cache if exists
    if product_id in products_cache:
        del products_cache[product_id]
        
    db.delete(db_product)
    db.commit()
    
    return {"message": "Product deleted successfully"}


@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a CSV file to create products.
    
    Expected CSV format:
    product_name,component_name,material,weight_kg
    
    Products with the same name in the CSV will be grouped together.
    Environmental impact is calculated automatically based on material.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    content = await file.read()
    decoded = content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))
    
    # Check required columns
    required_columns = {'product_name', 'component_name', 'material', 'weight_kg'}
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
        material = row['material'].strip()
        products_dict[product_name].append({
            'name': row['component_name'].strip(),
            'material': material,
            'weight_kg': float(row['weight_kg']),
            'environmental_impact': get_material_impact(material),
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
    
    if scoring_request.strategy == "custom":
        strategy = CustomStrategy(scoring_request.custom_weights)
    else:
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
