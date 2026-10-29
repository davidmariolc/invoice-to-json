import {
  BracketsCurlyIcon,
  CodeIcon,
  WarningCircleIcon,
} from "@phosphor-icons/react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { Spinner } from "@/components/ui/spinner";
import type { InvoiceProcessingState } from "@/features/invoices/schemas";

interface InvoiceOutputProps {
  state: InvoiceProcessingState;
}

const statusLabels: Record<InvoiceProcessingState["status"], string> = {
  error: "No se pudo procesar la factura",
  example: "Ejemplo ilustrativo. Datos ficticios.",
  idle: "Esperando una factura",
  loading: "Extrayendo los datos de la factura…",
  success: "Factura procesada. Revisa los datos extraídos.",
};

const getBadgeLabel = (status: InvoiceProcessingState["status"]) => {
  if (status === "example") {
    return "Ejemplo";
  }
  return status === "loading" ? "Procesando" : "JSON";
};

const InvoiceOutputBody = ({ state }: InvoiceOutputProps) => {
  if (state.status === "success" || state.status === "example") {
    return (
      <pre
        aria-label={
          state.status === "example"
            ? "Datos de la factura de ejemplo"
            : "Resultado del procesamiento"
        }
        className="max-h-[32rem] overflow-auto p-5 font-mono text-xs leading-6"
      >
        <code>{JSON.stringify(state.data, null, 2)}</code>
      </pre>
    );
  }

  if (state.status === "error") {
    return (
      <div className="flex min-h-64 flex-1 items-center p-5">
        <Alert variant="destructive">
          <WarningCircleIcon aria-hidden="true" />
          <AlertTitle>No se pudo procesar la factura</AlertTitle>
          <AlertDescription>{state.message}</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (state.status === "loading") {
    return (
      <Empty className="min-h-64">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <Spinner aria-label="Extrayendo datos" />
          </EmptyMedia>
          <EmptyTitle>Leyendo tu factura</EmptyTitle>
          <EmptyDescription>
            Estamos extrayendo sus datos. Esto puede tardar unos segundos.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  return (
    <Empty className="min-h-64">
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <BracketsCurlyIcon aria-hidden="true" />
        </EmptyMedia>
        <EmptyTitle>Tu resultado aparecerá aquí</EmptyTitle>
        <EmptyDescription>
          Sube una imagen de tu factura para consultar sus datos en este panel.
        </EmptyDescription>
      </EmptyHeader>
    </Empty>
  );
};

export const InvoiceOutput = ({ state }: InvoiceOutputProps) => (
  <Card
    aria-busy={state.status === "loading"}
    className="min-w-0 gap-6 [--card-spacing:--spacing(6)]"
  >
    <CardHeader>
      <p className="text-muted-foreground mb-2 font-mono text-[10px] tracking-widest">
        02 / RESULTADO
      </p>
      <CardTitle>
        <h2>Datos de la factura</h2>
      </CardTitle>
      <CardDescription>
        La información extraída, organizada en JSON.
      </CardDescription>
      <CardAction>
        <Badge variant="outline">{getBadgeLabel(state.status)}</Badge>
      </CardAction>
    </CardHeader>
    <CardContent className="flex min-h-80 flex-1 flex-col">
      <div className="bg-muted/25 flex min-w-0 flex-1 flex-col border">
        <div className="text-muted-foreground flex items-center gap-2 border-b px-4 py-3 font-mono text-[10px]">
          <CodeIcon aria-hidden="true" size={14} />
          resultado.json
        </div>
        <InvoiceOutputBody state={state} />
      </div>
    </CardContent>
    <CardFooter className="text-muted-foreground gap-2">
      <span
        aria-hidden="true"
        className="bg-muted-foreground/45 size-1.5 shrink-0 rounded-full"
      />
      <output className="text-[11px]">{statusLabels[state.status]}</output>
    </CardFooter>
  </Card>
);
