import { z } from "zod";

import { invoiceProcessResponseSchema } from "@/features/invoices/schemas";
import type { InvoiceProcessResponse } from "@/features/invoices/schemas";

const apiErrorSchema = z.object({ detail: z.string() });

export const processInvoice = async (
  file: File
): Promise<InvoiceProcessResponse> => {
  const body = new FormData();
  body.append("file", file);

  let response: Response;
  try {
    response = await fetch("/api/v1/invoices/process", {
      body,
      method: "POST",
      signal: AbortSignal.timeout(90_000),
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "TimeoutError") {
      throw new Error(
        "El procesamiento está tardando demasiado. Intenta de nuevo.",
        { cause: error }
      );
    }
    throw new Error(
      "No se pudo conectar con el servidor. Comprueba tu conexión e intenta de nuevo.",
      { cause: error }
    );
  }

  let payload: unknown;
  try {
    payload = await response.json();
  } catch (error) {
    throw new Error(
      "El servidor no devolvió una respuesta válida. Comprueba que FastAPI esté disponible.",
      { cause: error }
    );
  }

  if (!response.ok) {
    const error = apiErrorSchema.safeParse(payload);
    throw new Error(
      error.success
        ? error.data.detail
        : "No se pudo procesar la factura. Intenta de nuevo."
    );
  }

  const result = invoiceProcessResponseSchema.safeParse(payload);
  if (!result.success) {
    throw new Error(
      "La respuesta del servidor no tiene el formato de factura esperado."
    );
  }
  return result.data;
};
