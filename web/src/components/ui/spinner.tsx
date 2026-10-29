import { SpinnerIcon } from "@phosphor-icons/react";
import { cn } from "cn";

const Spinner = ({ className, ...props }: React.ComponentProps<"output">) => (
  <output
    aria-label="Cargando"
    className={cn("inline-flex size-4 shrink-0", className)}
    data-slot="spinner"
    {...props}
  >
    <SpinnerIcon
      aria-hidden="true"
      className="size-full animate-spin motion-reduce:animate-none"
    />
  </output>
);

export { Spinner };
