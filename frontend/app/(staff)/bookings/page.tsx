import { ServiceHealthPanel } from "@/components/shared/ServiceHealthPanel";
import { tStaff } from "@/lib/i18n/staffNav";

export default function BookingsPage() {
  return (
    <ServiceHealthPanel
      title={tStaff("navBookings")}
      service="bookings"
      loadingMessage={tStaff("serviceHealthLoading")}
      statusUpText={tStaff("serviceHealthUp")}
      statusDownText={tStaff("serviceHealthDown")}
      unknownStatusText={tStaff("serviceHealthUnknown")}
      statusLabelText={tStaff("serviceHealthStatus")}
      unavailableText={tStaff("serviceHealthDown")}
    />
  );
}
