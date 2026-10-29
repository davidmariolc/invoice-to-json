import { z } from "zod";

export const invoiceImageSchema = z
  .file({ error: "Selecciona una imagen de tu factura." })
  .mime(["image/jpeg", "image/png", "image/webp"], {
    error: "Elige una imagen JPG, PNG o WEBP.",
  })
  .min(1, { error: "La imagen está vacía. Selecciona otro archivo." })
  .max(4 * 1024 * 1024, { error: "La imagen no debe superar los 4 MB." });

export const invoiceFormSchema = z.object({ invoice: invoiceImageSchema });
export type InvoiceFormValues = z.infer<typeof invoiceFormSchema>;

const invoicePartySchema = z.object({
  address: z.string().nullable(),
  name: z.string().nullable(),
  tax_id: z.string().nullable(),
});

const invoiceItemSchema = z.object({
  amount: z.number().finite().nullable(),
  description: z.string().nullable(),
  quantity: z.number().finite().nullable(),
  unit_price: z.number().finite().nullable(),
});

export const invoiceDataSchema = z.object({
  currency: z.string().nullable(),
  invoice_number: z.string().nullable(),
  issue_date: z.iso.date().nullable(),
  issuer: invoicePartySchema,
  items: z.array(invoiceItemSchema),
  recipient: invoicePartySchema,
  subtotal: z.number().finite().nullable(),
  taxes: z.number().finite().nullable(),
  total: z.number().finite().nullable(),
});

export const invoiceProcessResponseSchema = z.object({
  data: invoiceDataSchema,
  filename: z.string(),
  model: z.string(),
});

export type InvoiceData = z.infer<typeof invoiceDataSchema>;
export type InvoiceProcessResponse = z.infer<
  typeof invoiceProcessResponseSchema
>;
export type InvoiceProcessingState =
  | { status: "idle" | "loading" }
  | { status: "example" | "success"; data: InvoiceData }
  | { status: "error"; message: string };
