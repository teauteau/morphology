import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function AboutPage() {
  return (
    <div className="min-h-screen flex flex-col items-center text-center p-6">
      {/* Navbar */}
      <nav className="w-full flex justify-between items-center p-4 border-b shadow-sm fixed top-0 left-0 bg-white z-50">
        <div className="text-2xl font-bold">[LOGO]</div>
        <div className="space-x-4">
          <Link href="/">
            <Button variant="ghost">Home</Button>
          </Link>
          <Link href="/generate">
            <Button variant="outline" className="bg-blue-200">Genereer</Button>
          </Link>
          <Link href="/about">
            <Button variant="ghost">Over</Button>
          </Link>
          <Link href="/contact">
            <Button variant="ghost">Contact</Button>
          </Link>
          <Link href="/help">
            <Button variant="ghost">Help</Button>
          </Link>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex flex-col items-center mt-24 max-w-3xl">
        <h1 className="text-4xl font-bold">Over MorphoAI</h1>
        <p className="mt-4 text-gray-600">
          {/* Add your description about the app here */}
        </p>
      </main>
    </div>
  );
}
