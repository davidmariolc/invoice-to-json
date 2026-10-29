from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class InvoiceSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class InvoiceParty(InvoiceSchema):
    name: str | None
    tax_id: str | None = Field(description="RUC, NIF u otro identificador fiscal, conservado como texto.")
    address: str | None


class InvoiceItem(InvoiceSchema):
    description: str | None
    quantity: float | None
    unit_price: float | None
    amount: float | None


class InvoiceData(InvoiceSchema):
    invoice_number: str | None
    issue_date: date | None = Field(description="Fecha de emisión en formato YYYY-MM-DD; null si no es legible o es ambigua.")
    currency: str | None = Field(description="Código de moneda ISO 4217, como PEN, USD o EUR; null si no se puede identificar.")
    issuer: InvoiceParty
    recipient: InvoiceParty
    items: list[InvoiceItem]
    subtotal: float | None
    taxes: float | None
    total: float | None


class InvoiceExtraction(InvoiceSchema):
    is_invoice: bool = Field(description="True si la imagen contiene una factura, boleta o recibo de venta legible; false para imágenes ajenas o ilegibles.")
    invoice: InvoiceData


class InvoiceProcessResponse(BaseModel):
    model: str
    filename: str
    data: InvoiceData
