import { SlideViewer } from "@/components/slides";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Forging - Presentation",
  description: "AI-Powered Game Coaching - Hackathon Presentation",
};

export default function SlidesPage() {
  return <SlideViewer />;
}
