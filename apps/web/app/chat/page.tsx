import { TutorChat } from "@/components/tutor-chat";
import { InkBackground } from "@/components/ink-background";

export default function Home() {
  return (
    <>
      <InkBackground withParticles={false} />
      <TutorChat />
    </>
  );
}
