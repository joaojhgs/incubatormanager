import { ServiceHealthPanel } from "@/components/shared/ServiceHealthPanel";
import { tStaff } from "@/lib/i18n/staffNav";

export default function ContractsPage() {
  return (
    <ServiceHealthPanel
      title={tStaff("navContracts")}
      service="contracts"
      loadingMessage={tStaff("serviceHealthLoading")}
      statusUpText={tStaff("serviceHealthUp")}
      statusDownText={tStaff("serviceHealthDown")}
      unknownStatusText={tStaff("serviceHealthUnknown")}
      unavailableText={tStaff("serviceHealthDown")}
    />
  );
}
