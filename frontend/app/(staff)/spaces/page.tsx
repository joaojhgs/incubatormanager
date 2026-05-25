import { ServiceHealthPanel } from "@/components/shared/ServiceHealthPanel";
import { tStaff } from "@/lib/i18n/staffNav";

export default function SpacesPage() {
  return (
    <ServiceHealthPanel
      title={tStaff("navSpaces")}
      service="spaces"
      loadingMessage={tStaff("serviceHealthLoading")}
      statusUpText={tStaff("serviceHealthUp")}
      statusDownText={tStaff("serviceHealthDown")}
      unknownStatusText={tStaff("serviceHealthUnknown")}
      unavailableText={tStaff("serviceHealthDown")}
    />
  );
}
