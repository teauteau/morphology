"use client";
import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function GeneratePage() {
  const [text, setText] = useState("");
  const [difficulty, setDifficulty] = useState<string | null>(null);
  const [language, setLanguage] = useState<"nl" | "en">("nl");

  const translations = {
    nl: {
      title: "Laten we de magie uitvoeren",
      step1: "1. Vul de tekst in waarmee u de opgaven wilt genereren.",
      placeholder: "Plak hier uw tekst...",
      step2: "2. Selecteer de moeilijkheidsgraad voor de opgaven.",
      easy: "Makkelijk",
      medium: "Gemiddeld",
      hard: "Moeilijk",
      generate: "Genereer",
    },
    en: {
      title: "Let's Perform the Magic",
      step1: "1. Enter the text to generate exercises.",
      placeholder: "Paste your text here...",
      step2: "2. Select the difficulty level for the exercises.",
      easy: "Easy",
      medium: "Medium",
      hard: "Hard",
      generate: "Generate",
    },
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center text-center p-6">
      {/* Navbar */}
      <nav className="w-full flex justify-between items-center p-4 border-b shadow-sm fixed top-0 left-0 bg-white z-50">
        <div className="text-2xl font-bold">[LOGO]</div>
        <div className="space-x-4">
          <Link href="/">
            <Button variant="ghost">Home</Button>
          </Link>
          <Link href="/generate">
            <Button variant="outline" className="bg-blue-200">
              {language === "nl" ? "Genereer" : "Generate"}
            </Button>
          </Link>
          <Link href="/about">
            <Button variant="ghost">{language === "nl" ? "Over" : "About"}</Button>
          </Link>
          <Link href="/contact">
            <Button variant="ghost">{language === "nl" ? "Contact" : "Contact"}</Button>
          </Link>
          <Link href="/help">
            <Button variant="ghost">{language === "nl" ? "Help" : "Help"}</Button>
          </Link>
          <Button onClick={() => setLanguage(language === "nl" ? "en" : "nl")}>
            {language === "nl" ? "English" : "Nederlands"}
          </Button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="mt-24 w-full max-w-3xl">
        <h1 className="text-4xl font-bold">{translations[language].title}</h1>
        <h2 className="text-xl font-bold mt-6">{translations[language].step1}</h2>

        <textarea
          className="w-full mt-4 p-3 border rounded-lg resize-none overflow-hidden"
          placeholder={translations[language].placeholder}
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            e.target.style.height = "auto"; // Reset height to recalculate
            e.target.style.height = e.target.scrollHeight + "px"; // Set new height
          }}
        />

        <h2 className="text-xl font-bold mt-6">{translations[language].step2}</h2>

        {/* Difficulty Buttons */}
        <div className="flex justify-center gap-4 mt-4">
          <button
            className={`px-6 py-2 rounded-lg text-white ${
              difficulty === "Makkelijk" ? "bg-green-600" : "bg-green-400"
            }`}
            onClick={() => setDifficulty(translations[language].easy)}
          >
            {translations[language].easy}
          </button>
          <button
            className={`px-6 py-2 rounded-lg text-white ${
              difficulty === "Gemiddeld" ? "bg-orange-600" : "bg-orange-400"
            }`}
            onClick={() => setDifficulty(translations[language].medium)}
          >
            {translations[language].medium}
          </button>
          <button
            className={`px-6 py-2 rounded-lg text-white ${
              difficulty === "Moeilijk" ? "bg-red-600" : "bg-red-400"
            }`}
            onClick={() => setDifficulty(translations[language].hard)}
          >
            {translations[language].hard}
          </button>
        </div>

        {/* Generate Button */}
        <button
          className={`mt-6 px-8 py-3 rounded-lg text-white ${
            text && difficulty ? "bg-gray-800" : "bg-gray-400 cursor-not-allowed"
          }`}
          disabled={!text || !difficulty}
        >
          {translations[language].generate}
        </button>
      </main>
    </div>
  );
}
