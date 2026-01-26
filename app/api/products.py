import csv
import io
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Response
from sqlalchemy.orm import Session

from app.models.schemas import (
    ProductCreate,
    ProductResponse,
    ScoringRequest,
    ScoreResponse,
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
    
    # Apply badges using Decorator Pattern if provided
    if product_data.badges:
        for badge_key in product_data.badges:
            if badge_key in BADGE_MAP:
                badge_class = BADGE_MAP[badge_key]
                composite = badge_class(composite)
    
    products_cache[db_product.id] = composite
    
    # Calculate Average Score (decorators will affect the score via get_score_modifier)
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
    
    Optional columns:
    energy_consumption_mj,water_usage_liters,waste_generation_kg,
    recyclability_score,recycled_content_percentage
    
    Products with the same name in the CSV will be grouped together.
    Environmental impact is calculated automatically based on material.
    scores are calculated automatically for each product.
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
        
        # Helper to safely parse floats
        def parse_float(key: str) -> float:
            val = row.get(key)
            if val and val.strip():
                try:
                    return float(val)
                except ValueError:
                    return 0.0
            return 0.0

        products_dict[product_name].append({
            'name': row['component_name'].strip(),
            'material': material,
            'weight_kg': float(row['weight_kg']),
            'environmental_impact': get_material_impact(material),
            'energy_consumption_mj': parse_float('energy_consumption_mj'),
            'water_usage_liters': parse_float('water_usage_liters'),
            'waste_generation_kg': parse_float('waste_generation_kg'),
            'recyclability_score': parse_float('recyclability_score'),
            'recycled_content_percentage': parse_float('recycled_content_percentage'),
        })
    
    # Create products
    created_products = []
    for product_name, components in products_dict.items():
        # Create database product
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
                energy_consumption_mj=comp['energy_consumption_mj'],
                water_usage_liters=comp['water_usage_liters'],
                waste_generation_kg=comp['waste_generation_kg'],
                recyclability_score=comp['recyclability_score'],
                recycled_content_percentage=comp['recycled_content_percentage'],
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


@router.get("/report/pdf")
def generate_pdf_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a PDF report for all user products.
    
    Returns a PDF file as binary response that can be downloaded directly.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    
    products = db.query(Product).filter(Product.user_id == current_user.id).all()
    
    if not products:
        raise HTTPException(status_code=404, detail="No products found")
    
    # Create PDF buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor('#1a5f2a')
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=10,
        textColor=colors.grey
    )
    product_title_style = ParagraphStyle(
        'ProductTitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10,
        spaceBefore=15,
        textColor=colors.HexColor('#2d5a3d')
    )
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading3'],
        fontSize=11,
        spaceAfter=5,
        spaceBefore=10,
        textColor=colors.HexColor('#444444')
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=3
    )
    
    # Build content
    content = []
    
    # Title
    content.append(Paragraph("🌿 Sustainability Report", title_style))
    content.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
    content.append(Paragraph(f"User: {current_user.email} | Total Products: {len(products)}", subtitle_style))
    content.append(Spacer(1, 10*mm))
    
    total_avg_score = 0
    
    for idx, db_product in enumerate(products, 1):
        # Product header
        content.append(Paragraph(f"Product #{idx}: {db_product.name}", product_title_style))
        content.append(Paragraph(f"Average Score: <b>{db_product.average_score or 'N/A'}</b>", normal_style))
        
        # Components table
        if db_product.components:
            content.append(Paragraph("Components", section_style))
            
            table_data = [['Name', 'Material', 'Weight (kg)', 'Impact']]
            for comp in db_product.components:
                table_data.append([
                    comp.name[:20],
                    comp.material[:20],
                    f"{comp.weight_kg:.3f}",
                    f"{comp.environmental_impact:.2f}"
                ])
            
            table = Table(table_data, colWidths=[50*mm, 50*mm, 30*mm, 25*mm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d5a3d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fdf9')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fdf9'), colors.white]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ]))
            content.append(table)
            
            # Environmental metrics
            content.append(Paragraph("Environmental Metrics", section_style))
            
            total_energy = sum(c.energy_consumption_mj for c in db_product.components)
            total_water = sum(c.water_usage_liters for c in db_product.components)
            total_waste = sum(c.waste_generation_kg for c in db_product.components)
            avg_recyclability = sum(c.recyclability_score for c in db_product.components) / len(db_product.components)
            
            metrics_data = [
                ['Energy Consumption', f"{total_energy:.2f} MJ"],
                ['Water Usage', f"{total_water:.2f} L"],
                ['Waste Generation', f"{total_waste:.3f} kg"],
                ['Avg Recyclability', f"{avg_recyclability:.1f}%"]
            ]
            
            metrics_table = Table(metrics_data, colWidths=[50*mm, 40*mm])
            metrics_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ]))
            content.append(metrics_table)
        
        if db_product.average_score:
            total_avg_score += db_product.average_score
        
        content.append(Spacer(1, 5*mm))
    
    # Overall summary
    content.append(Spacer(1, 10*mm))
    content.append(Paragraph("Overall Summary", product_title_style))
    
    overall_avg = total_avg_score / len(products) if products else 0
    summary_data = [
        ['Total Products', str(len(products))],
        ['Overall Average Score', f"{overall_avg:.1f}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[60*mm, 40*mm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f5e9')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2d5a3d')),
    ]))
    content.append(summary_table)
    
    # Build PDF
    doc.build(content)
    
    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    filename = f"sustainability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
        }
    )

