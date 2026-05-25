import { ServiceHealthPanel } from "@/components/shared/ServiceHealthPanel";
import { tStaff } from "@/lib/i18n/staffNav";

export default function StaffDashboardPage() {
  return (
    <ServiceHealthPanel
      title={tStaff("pageHomeTitle")}
      service="dashboard"
      loadingMessage={tStaff("serviceHealthLoading")}
      statusUpText={tStaff("serviceHealthUp")}
      statusDownText={tStaff("serviceHealthDown")}
      unknownStatusText={tStaff("serviceHealthUnknown")}
      statusLabelText={tStaff("serviceHealthStatus")}
      unavailableText={tStaff("serviceHealthDown")}
    />
  );
}
