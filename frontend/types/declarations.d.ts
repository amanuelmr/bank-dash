// Static image imports (the app mostly references /public paths as plain URLs).
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
