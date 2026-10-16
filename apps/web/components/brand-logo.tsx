import Image from "next/image";

/** The accompanying brand name provides the accessible label. */
export function BrandLogo({className = "h-10 w-10"}: {className?: string}) {
  return <span aria-hidden="true" className={`inline-flex shrink-0 items-center justify-center rounded-lg bg-paper-100 ${className}`}>
    <Image src="/brand/luojia-logo.png" width={1254} height={1254} alt="" priority sizes="48px" className="h-full w-full object-contain" />
  </span>;
}
