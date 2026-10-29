import { ArrowRightIcon, ReceiptIcon } from "@phosphor-icons/react";
import { useState } from "react";

import { processInvoice } from "@/features/invoices/api";
import { InvoiceOutput } from "@/features/invoices/components/invoice-output";
import { InvoiceUploadForm } from "@/features/invoices/components/invoice-upload-form";
import { exampleInvoice } from "@/features/invoices/example";
import type { InvoiceProcessingState } from "@/features/invoices/schemas";

const App = () => {
  const [processingState, setProcessingState] =
    useState<InvoiceProcessingState>({
      data: exampleInvoice.data,
      status: "example",
    });

  const handleUpload = async (file: File) => {
    setProcessingState({ status: "loading" });
    try {
      const response = await processInvoice(file);
      setProcessingState({ data: response.data, status: "success" });
    } catch (error) {
      setProcessingState({
        message:
          error instanceof Error
            ? error.message
            : "No se pudo procesar la factura.",
        status: "error",
      });
    }
  };

  const handleImageChange = () => setProcessingState({ status: "idle" });
  const handleReset = () =>
    setProcessingState({ data: exampleInvoice.data, status: "example" });

  return (
    <div className="bg-background min-h-svh">
      <header className="border-b">
        <div className="mx-auto flex h-20 max-w-6xl items-center justify-between gap-4 px-5 sm:px-8">
          <a
            aria-label="Invoice to JSON, inicio"
            className="flex items-center gap-3"
            href="/"
          >
            <span className="bg-primary text-primary-foreground flex size-9 items-center justify-center">
              <ReceiptIcon aria-hidden="true" size={21} />
            </span>
            <span className="text-sm font-semibold tracking-tight">
              invoice
              <span className="text-muted-foreground px-1.5 font-normal">
                /
              </span>
              json
            </span>
          </a>
          <span className="text-muted-foreground hidden font-mono text-[11px] tracking-wider sm:block">
            MENOS TRABAJO MANUAL.
          </span>
        </div>
      </header>
      <main className="mx-auto flex max-w-6xl flex-col gap-9 px-5 py-10 sm:px-8 sm:py-14">
        <div className="flex flex-col gap-4">
          <p className="text-muted-foreground font-mono text-[10px] tracking-[0.18em]">
            DE DOCUMENTO A DATOS
          </p>
          <h1 className="max-w-2xl text-3xl font-medium tracking-tight sm:text-4xl">
            Una factura. Todos sus datos.
          </h1>
          <p className="text-muted-foreground max-w-xl text-sm leading-6">
            Sube la imagen de una factura y consulta el resultado de su
            procesamiento en formato JSON, en un solo lugar.
          </p>
        </div>
        <div className="grid items-stretch gap-6 md:grid-cols-2">
          <InvoiceUploadForm
            isExample={processingState.status === "example"}
            isProcessing={processingState.status === "loading"}
            onImageChange={handleImageChange}
            onReset={handleReset}
            onUpload={handleUpload}
          />
          <InvoiceOutput state={processingState} />
        </div>
        <footer className="text-muted-foreground flex flex-wrap items-center justify-between gap-3 text-xs">
          <span className="flex items-center gap-2">
            Imagen de tu factura
            <ArrowRightIcon aria-hidden="true" />
            Datos estructurados
          </span>
          <span className="font-mono text-[10px] tracking-wider">
            INVOICE TO JSON
          </span>
        </footer>
      </main>
    </div>
  );
};

export default App;
