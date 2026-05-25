import { ServiceHealthPanel } from "@/components/shared/ServiceHealthPanel";
import { tStaff } from "@/lib/i18n/staffNav";

export default function FinancePage() {
  return (
    <ServiceHealthPanel
      title={tStaff("navFinance")}
      service="finance"
      loadingMessage={tStaff("serviceHealthLoading")}
      statusUpText={tStaff("serviceHealthUp")}
      statusDownText={tStaff("serviceHealthDown")}
      unknownStatusText={tStaff("serviceHealthUnknown")}
      statusLabelText={tStaff("serviceHealthStatus")}
      unavailableText={tStaff("serviceHealthDown")}
    />
  );
}
