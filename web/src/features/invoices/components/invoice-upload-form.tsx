import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowUpRightIcon,
  FileImageIcon,
  UploadSimpleIcon,
  XIcon,
} from "@phosphor-icons/react";
import { useEffect, useRef, useState } from "react";
import { useController, useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import {
  invoiceFormSchema,
  invoiceImageSchema,
} from "@/features/invoices/schemas";
import type { InvoiceFormValues } from "@/features/invoices/schemas";

interface InvoiceUploadFormProps {
  isProcessing: boolean;
  onImageChange: () => void;
  onUpload: (file: File) => Promise<void>;
}

export const InvoiceUploadForm = ({
  isProcessing,
  onImageChange,
  onUpload,
}: InvoiceUploadFormProps) => {
  const { control, handleSubmit, reset, setError, setValue } =
    useForm<InvoiceFormValues>({ resolver: zodResolver(invoiceFormSchema) });
  const {
    field: {
      name: imageName,
      onBlur: handleImageBlur,
      ref: imageRef,
      value: selectedFile,
    },
    fieldState,
  } = useController({ control, name: "invoice" });
  const [preview, setPreview] = useState<string | null>(null);
  const [isPreviewReady, setIsPreviewReady] = useState(false);
  const previewUrl = useRef<string | null>(null);

  useEffect(
    () => () => {
      if (previewUrl.current) {
        URL.revokeObjectURL(previewUrl.current);
      }
    },
    []
  );

  const clearPreview = () => {
    if (previewUrl.current) {
      URL.revokeObjectURL(previewUrl.current);
    }
    previewUrl.current = null;
    setPreview(null);
    setIsPreviewReady(false);
  };

  const selectFile = (file: File) => {
    clearPreview();
    onImageChange();
    setValue("invoice", file, { shouldDirty: true, shouldValidate: true });
    if (invoiceImageSchema.safeParse(file).success) {
      const url = URL.createObjectURL(file);
      previewUrl.current = url;
      setPreview(url);
    }
  };

  const resetForm = () => {
    reset();
    clearPreview();
    onImageChange();
  };

  return (
    <Card className="min-w-0 gap-6 [--card-spacing:--spacing(6)]">
      <CardHeader>
        <p className="text-muted-foreground mb-2 font-mono text-[10px] tracking-widest">
          01 / DOCUMENTO
        </p>
        <CardTitle>
          <h2>Sube tu factura</h2>
        </CardTitle>
        <CardDescription>
          Empieza con una imagen clara y legible.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col gap-4">
        <form
          id="invoice-upload-form"
          noValidate
          onReset={resetForm}
          onSubmit={handleSubmit(async ({ invoice }) => {
            if (!preview || !isPreviewReady) {
              setError("invoice", {
                message:
                  "Selecciona una imagen válida antes de subir la factura.",
              });
              return;
            }
            await onUpload(invoice);
          })}
        >
          <FieldGroup>
            <Field
              data-disabled={isProcessing}
              data-invalid={fieldState.invalid}
            >
              <FieldLabel htmlFor="invoice-image">
                Imagen de la factura
              </FieldLabel>
              <div className="border-input bg-muted/25 focus-within:outline-ring hover:bg-muted/50 relative flex min-h-64 flex-col items-center justify-center gap-4 border border-dashed p-5 text-center transition-colors focus-within:outline-2 focus-within:outline-offset-2">
                <Input
                  accept="image/jpeg,image/png,image/webp"
                  aria-describedby={
                    fieldState.invalid
                      ? "invoice-help invoice-error"
                      : "invoice-help"
                  }
                  aria-invalid={fieldState.invalid}
                  className="absolute inset-0 h-full cursor-pointer opacity-0"
                  disabled={isProcessing}
                  id="invoice-image"
                  name={imageName}
                  onBlur={handleImageBlur}
                  onChange={(event) => {
                    const file = event.currentTarget.files?.[0];
                    if (file) {
                      selectFile(file);
                    }
                  }}
                  ref={imageRef}
                  type="file"
                />
                {preview ? (
                  <img
                    alt={`Vista previa de ${selectedFile?.name ?? "la factura"}`}
                    className="max-h-44 max-w-full object-contain"
                    onError={() => {
                      clearPreview();
                      setError("invoice", {
                        message:
                          "No se pudo leer esta imagen. Selecciona otro archivo.",
                      });
                    }}
                    onLoad={() => setIsPreviewReady(true)}
                    src={preview}
                  />
                ) : (
                  <span className="bg-background text-muted-foreground flex size-12 items-center justify-center border">
                    <UploadSimpleIcon
                      aria-hidden="true"
                      size={24}
                      weight="light"
                    />
                  </span>
                )}
                <div className="pointer-events-none flex flex-col gap-1">
                  <p className="text-xs font-medium">
                    {preview
                      ? "Haz clic para cambiar la imagen"
                      : "Haz clic para seleccionar una imagen"}
                  </p>
                  <p className="text-muted-foreground text-[11px]">
                    Una foto o captura de tu factura
                  </p>
                </div>
              </div>
              <FieldDescription id="invoice-help">
                JPG, PNG o WEBP · Máximo 4 MB
              </FieldDescription>
              {fieldState.error && (
                <FieldError errors={[fieldState.error]} id="invoice-error" />
              )}
            </Field>
            {preview && (
              <div className="bg-muted/20 flex min-w-0 items-center gap-3 border p-3">
                <FileImageIcon
                  aria-hidden="true"
                  className="text-muted-foreground shrink-0"
                  size={20}
                />
                <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                  <p className="truncate text-xs font-medium">
                    {selectedFile?.name}
                  </p>
                  <p className="text-muted-foreground text-[11px]">
                    {((selectedFile?.size ?? 0) / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <Button
                  aria-label="Quitar imagen"
                  disabled={isProcessing}
                  form="invoice-upload-form"
                  size="icon-sm"
                  type="reset"
                  variant="ghost"
                >
                  <XIcon aria-hidden="true" />
                </Button>
              </div>
            )}
          </FieldGroup>
        </form>
      </CardContent>
      <CardFooter className="flex flex-col items-stretch gap-3">
        <Button
          disabled={isProcessing || (preview !== null && !isPreviewReady)}
          form="invoice-upload-form"
          size="lg"
          type="submit"
        >
          {isProcessing ? (
            <Spinner aria-hidden="true" data-icon="inline-start" />
          ) : (
            <ArrowUpRightIcon aria-hidden="true" data-icon="inline-start" />
          )}
          {isProcessing ? "Procesando factura…" : "Subir factura"}
        </Button>
        <p className="text-muted-foreground text-center text-[11px] leading-5">
          Asegúrate de que todos los datos sean visibles.
        </p>
      </CardFooter>
    </Card>
  );
};
