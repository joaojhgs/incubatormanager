import { ServiceHealthPanel } from "@/components/shared/ServiceHealthPanel";
import { tClient } from "@/lib/i18n/clientPortal";

export default function ClientBookingsPage() {
  return (
    <ServiceHealthPanel
      title={tClient("pageBookingsTitle")}
      service="bookings"
      loadingMessage={tClient("pageLoading")}
      statusUpText={tClient("serviceHealthUp")}
      statusDownText={tClient("serviceHealthDown")}
      unknownStatusText={tClient("serviceHealthUnavailable")}
      unavailableText={tClient("serviceUnavailable")}
    />
  );
}
