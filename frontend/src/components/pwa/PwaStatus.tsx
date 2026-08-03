import { OfflineBanner } from "./OfflineBanner";
import { UpdatePrompt } from "./UpdatePrompt";

export function PwaStatus() {
  return (
    <>
      <OfflineBanner />
      <UpdatePrompt />
    </>
  );
}
