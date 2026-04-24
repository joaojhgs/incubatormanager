import { tClient } from "@/lib/i18n/clientPortal";

export default function ClientPortalHomePage() {
  return <p>{tClient("homeIntro")}</p>;
}
