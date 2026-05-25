import { ServiceHealthPanel } from "@/components/shared/ServiceHealthPanel";
import { tClient } from "@/lib/i18n/clientPortal";

export default function ClientContractPage() {
  return (
    <ServiceHealthPanel
      title={tClient("pageContractTitle")}
      service="contracts"
      loadingMessage={tClient("pageLoading")}
      statusUpText={tClient("serviceHealthUp")}
      statusDownText={tClient("serviceHealthDown")}
      unknownStatusText={tClient("serviceHealthUnavailable")}
      unavailableText={tClient("serviceHealthHint")}
    />
  );
}
