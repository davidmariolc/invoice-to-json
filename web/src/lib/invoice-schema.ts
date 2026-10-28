import { z } from "zod";

export const invoiceImageSchema = z
  .file({ error: "Selecciona una imagen de tu factura." })
  .mime(["image/jpeg", "image/png", "image/webp"], {
    error: "Elige una imagen JPG, PNG o WEBP.",
  })
  .min(1, { error: "La imagen está vacía. Selecciona otro archivo." })
  .max(10 * 1024 * 1024, { error: "La imagen no debe superar los 10 MB." });

export const invoiceFormSchema = z.object({ invoice: invoiceImageSchema });
export type InvoiceFormValues = z.infer<typeof invoiceFormSchema>;
