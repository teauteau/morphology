"use client";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export default function HomePage() {
  const translations = {
    nl: {
      home: "Home",
      generate: "Genereer",
      about: "Over",
      contact: "Contact",
      help: "Help",
      title: "MorphoAi",
      description:
        "Een interactieve tool voor leerkrachten om hen te helpen bij het maken van opgaven op het gebied van morfologie aan de hand van een geïmporteerde tekst.",
      start: "Start",
    },
    en: {
      home: "Home",
      generate: "Generate",
      about: "About",
      contact: "Contact",
      help: "Help",
      title: "MorphoAi",
      description:
        "An interactive tool for teachers that helps them create morphology-based exercises using an imported text.",
      start: "Start",
    },
  } as const;

  type Language = keyof typeof translations;
  const [language, setLanguage] = useState<Language>("nl");

  return (
    <div className="min-h-screen flex flex-col items-center justify-center text-center p-6">
      {/* Navbar */}
      <nav className="w-full flex justify-between items-center p-4 border-b shadow-sm fixed top-0 left-0 bg-white z-50">
        <div className="text-2xl font-bold">[LOGO]</div>
        <div className="space-x-4">
          <Link href="/">
            <Button variant="ghost">{translations[language].home}</Button>
          </Link>
          <Link href="/generate">
            <Button variant="outline" className="bg-blue-200">{translations[language].generate}</Button>
          </Link>
          <Link href="/about">
            <Button variant="ghost">{translations[language].about}</Button>
          </Link>
          <Link href="/contact">
            <Button variant="ghost">{translations[language].contact}</Button>
          </Link>
          <Link href="/help">
            <Button variant="ghost">{translations[language].help}</Button>
          </Link>
          <Button onClick={() => setLanguage(language === "nl" ? "en" : "nl")}>
            {language === "nl" ? "English" : "Nederlands"}
          </Button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex flex-col items-center mt-24">
        <h1 className="text-4xl font-bold">{translations[language].title}</h1>
        <p className="mt-4 text-gray-600 max-w-xl">{translations[language].description}</p>
        <Link href="/generate">
          <Button className="mt-6 bg-cyan-400 text-black px-6 py-3 text-lg rounded-lg shadow-md">
            {translations[language].start}
          </Button>
        </Link>
      </main>
    </div>
  );
}
