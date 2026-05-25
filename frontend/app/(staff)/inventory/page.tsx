import { ServiceHealthPanel } from "@/components/shared/ServiceHealthPanel";
import { tStaff } from "@/lib/i18n/staffNav";

export default function InventoryPage() {
  return (
    <ServiceHealthPanel
      title={tStaff("navInventory")}
      service="inventory"
      loadingMessage={tStaff("serviceHealthLoading")}
      statusUpText={tStaff("serviceHealthUp")}
      statusDownText={tStaff("serviceHealthDown")}
      unknownStatusText={tStaff("serviceHealthUnknown")}
      unavailableText={tStaff("serviceHealthDown")}
    />
  );
}
