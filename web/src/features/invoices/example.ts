import exampleImage from "@/assets/invoice-example.svg";
import { invoiceDataSchema } from "@/features/invoices/schemas";

export const exampleInvoice = {
  data: invoiceDataSchema.parse({
    currency: "PEN",
    invoice_number: "DEMO-000123",
    issue_date: "2026-10-29",
    issuer: { address: null, name: "Empresa Ejemplo", tax_id: null },
    items: [
      {
        amount: 100,
        description: "Servicio de prueba",
        quantity: 2,
        unit_price: 50,
      },
    ],
    recipient: { address: null, name: "Cliente Demo", tax_id: null },
    subtotal: 100,
    taxes: 18,
    total: 118,
  }),
  imageUrl: exampleImage,
};
