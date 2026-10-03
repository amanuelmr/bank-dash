declare module "*.svg" {
  import React from "react";
  const ReactComponent: React.FC<React.SVGProps<SVGSVGElement>>;
  export default ReactComponent;
}

declare module "*.png" {
  import type { StaticImageData } from "next/image";
  const value: StaticImageData;
  export default value;
}

declare module "*.jpg" {
  import type { StaticImageData } from "next/image";
  const value: StaticImageData;
  export default value;
}

declare module "*.jpeg" {
  import type { StaticImageData } from "next/image";
  const value: StaticImageData;
  export default value;
}
