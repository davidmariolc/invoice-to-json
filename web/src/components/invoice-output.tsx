import { BracketsCurlyIcon, CodeIcon } from "@phosphor-icons/react";

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

interface InvoiceOutputProps {
  result?: Record<string, unknown> | null;
}

export const InvoiceOutput = ({ result = null }: InvoiceOutputProps) => (
  <Card className="min-w-0 gap-6 [--card-spacing:--spacing(6)]">
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
        <Badge variant="outline">JSON</Badge>
      </CardAction>
    </CardHeader>
    <CardContent className="flex min-h-80 flex-1 flex-col">
      <div className="bg-muted/25 flex flex-1 flex-col border">
        <div className="text-muted-foreground flex items-center gap-2 border-b px-4 py-3 font-mono text-[10px]">
          <CodeIcon aria-hidden="true" size={14} />
          resultado.json
        </div>
        {result ? (
          <pre
            aria-label="Resultado del procesamiento"
            className="max-h-[32rem] overflow-auto p-5 font-mono text-xs leading-6"
          >
            <code>{JSON.stringify(result, null, 2)}</code>
          </pre>
        ) : (
          <Empty className="min-h-64">
            <EmptyHeader>
              <EmptyMedia variant="icon">
                <BracketsCurlyIcon aria-hidden="true" />
              </EmptyMedia>
              <EmptyTitle>Tu resultado aparecerá aquí</EmptyTitle>
              <EmptyDescription>
                Cuando se procese una factura, podrás consultar sus datos en
                este panel.
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        )}
      </div>
    </CardContent>
    <CardFooter className="text-muted-foreground gap-2">
      <span
        aria-hidden="true"
        className="bg-muted-foreground/45 size-1.5 shrink-0 rounded-full"
      />
      <p className="text-[11px]">
        {result
          ? "Resultado del procesamiento"
          : "Esperando una factura procesada"}
      </p>
    </CardFooter>
  </Card>
);
