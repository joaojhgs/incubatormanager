import { ServiceHealthPanel } from "@/components/shared/ServiceHealthPanel";
import { tClient } from "@/lib/i18n/clientPortal";

export default function ClientPaymentsPage() {
  return (
    <ServiceHealthPanel
      title={tClient("pagePaymentsTitle")}
      service="finance"
      loadingMessage={tClient("pageLoading")}
      statusUpText={tClient("serviceHealthUp")}
      statusDownText={tClient("serviceHealthDown")}
      unknownStatusText={tClient("serviceHealthUnavailable")}
      unavailableText={tClient("serviceUnavailable")}
    />
  );
}
