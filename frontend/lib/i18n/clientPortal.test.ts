import { describe, expect, it } from "vitest";

import { tClient } from "./clientPortal";
import { tPublicBooking } from "./publicBooking";

describe("client/public i18n", () => {
  it("exposes client ticket workflow labels", () => {
    expect(tClient("portalTicketNewTitle")).toBe("Novo pedido de suporte");
    expect(tClient("portalTicketDetailTitle")).toBe("Detalhe do pedido");
    expect(tClient("portalTicketNoMessages")).toBe("Ainda não existem mensagens neste pedido.");
  });

  it("exposes public booking form labels", () => {
    expect(tPublicBooking("pageTitle")).toBe("Pedido público de reserva");
    expect(tPublicBooking("requesterEmailInvalid")).toBe("Indique um email válido.");
    expect(tPublicBooking("submit")).toBe("Submeter pedido");
  });
});
