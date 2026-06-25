import { useMemo, useState } from "react"
import type { FormEvent } from "react"
import {
  Check,
  Copy,
  Loader2,
  Moon,
  RotateCcw,
  SlidersHorizontal,
  Sparkles,
  Sun,
  Volume2,
  WandSparkles,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { useTheme } from "@/components/theme-provider"

type GeneratePantunResponse = {
  pantun: string
}

type SliderFieldProps = {
  label: string
  helper: string
  value: number
  min: number
  max: number
  step: number
  onChange: (value: number) => void
}

const EXAMPLE_THEMES = [
  "pendidikan",
  "persahabatan",
  "teknologi",
  "alam",
  "keluarga",
  "cita-cita",
]

const DEFAULT_SETTINGS = {
  temperature: 0.9,
  topK: 50,
  topP: 0.95,
  maxNewTokens: 80,
}

function SliderField({
  label,
  helper,
  value,
  min,
  max,
  step,
  onChange,
}: SliderFieldProps) {
  return (
    <label className="grid gap-2">
      <div className="flex items-start justify-between gap-4">
        <div className="grid gap-0.5">
          <span className="text-sm font-medium">{label}</span>
          <span className="text-xs leading-5 text-muted-foreground">
            {helper}
          </span>
        </div>
        <span className="rounded-md border bg-background px-2 py-1 font-mono text-xs text-muted-foreground">
          {value}
        </span>
      </div>
      <input
        className="h-2 w-full cursor-pointer appearance-none rounded-full bg-muted accent-primary"
        max={max}
        min={min}
        step={step}
        type="range"
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  )
}

function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message
  }

  return "Terjadi error saat membuat pantun."
}

function speakPantun(pantun: string) {
  const text = pantun.trim()

  if (!text) {
    window.alert("Belum ada pantun untuk dibacakan.")
    return
  }

  if (typeof window.speechSynthesis === "undefined") {
    window.alert("Browser ini belum mendukung fitur speech audio.")
    return
  }

  window.speechSynthesis.cancel()

  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = "id-ID"
  utterance.rate = 0.95
  utterance.pitch = 1

  const voices = window.speechSynthesis.getVoices()
  const preferredVoice = voices.find((voice) => {
    const name = voice.name.toLowerCase()
    const lang = voice.lang.toLowerCase()

    return (
      lang.startsWith("id") &&
      (name.includes("natural") ||
        name.includes("online") ||
        name.includes("google") ||
        name.includes("microsoft"))
    )
  })
  const fallbackVoice =
    preferredVoice ||
    voices.find((voice) => voice.lang.toLowerCase().startsWith("id")) ||
    voices.find((voice) => voice.lang.toLowerCase().startsWith("ms"))

  if (fallbackVoice) {
    utterance.voice = fallbackVoice
  }

  window.speechSynthesis.speak(utterance)
}

function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const isDark = theme === "dark"

  return (
    <Button
      className="gap-2"
      size="sm"
      type="button"
      variant="outline"
      onClick={() => setTheme(isDark ? "light" : "dark")}
    >
      {isDark ? <Sun className="size-4" /> : <Moon className="size-4" />}
      {isDark ? "Light" : "Dark"}
    </Button>
  )
}

export function App() {
  const [tema, setTema] = useState("pendidikan")
  const [temperature, setTemperature] = useState(DEFAULT_SETTINGS.temperature)
  const [topK, setTopK] = useState(DEFAULT_SETTINGS.topK)
  const [topP, setTopP] = useState(DEFAULT_SETTINGS.topP)
  const [maxNewTokens, setMaxNewTokens] = useState(
    DEFAULT_SETTINGS.maxNewTokens
  )
  const [pantun, setPantun] = useState("")
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [hasCopied, setHasCopied] = useState(false)

  const pantunLines = useMemo(
    () => pantun.split("\n").filter((line) => line.trim().length > 0),
    [pantun]
  )
  const canGenerate = tema.trim().length > 0 && !isLoading

  function resetSettings() {
    setTemperature(DEFAULT_SETTINGS.temperature)
    setTopK(DEFAULT_SETTINGS.topK)
    setTopP(DEFAULT_SETTINGS.topP)
    setMaxNewTokens(DEFAULT_SETTINGS.maxNewTokens)
  }

  async function handleGenerate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")
    setHasCopied(false)

    if (!tema.trim()) {
      setError("Masukkan tema terlebih dahulu.")
      return
    }

    setIsLoading(true)

    try {
      const response = await fetch("/api/generate", {
        body: JSON.stringify({
          tema: tema.trim(),
          temperature,
          top_k: topK,
          top_p: topP,
          max_new_tokens: maxNewTokens,
        }),
        headers: {
          "Content-Type": "application/json",
        },
        method: "POST",
      })
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Gagal membuat pantun.")
      }

      setPantun((data as GeneratePantunResponse).pantun)
    } catch (currentError) {
      setError(getErrorMessage(currentError))
    } finally {
      setIsLoading(false)
    }
  }

  async function handleCopy() {
    if (!pantun.trim()) {
      return
    }

    await navigator.clipboard.writeText(pantun)
    setHasCopied(true)
    window.setTimeout(() => setHasCopied(false), 1600)
  }

  return (
    <main className="min-h-svh bg-muted/30 text-foreground">
      <div className="mx-auto grid w-full max-w-7xl gap-6 px-4 py-5 sm:px-6 lg:px-8">
        <header className="flex items-center justify-between gap-4 py-4">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
              <WandSparkles className="size-5" />
            </div>
            <div className="min-w-0">
              <h1 className="truncate text-lg font-semibold tracking-tight">
                PANTUN-AI
              </h1>
              <p className="truncate text-sm text-muted-foreground">
                Generator pantun berbasis model Python lokal
              </p>
            </div>
          </div>
          <ThemeToggle />
        </header>

        <section className="grid gap-6 lg:grid-cols-[minmax(320px,0.88fr)_minmax(0,1.12fr)]">
          <div className="grid gap-6">
            <Card className="shadow-sm">
              <CardHeader className="border-b">
                <div className="flex items-start justify-between gap-4">
                  <div className="grid gap-1">
                    <CardTitle className="text-xl">Buat pantun</CardTitle>
                    <CardDescription>Pilih tema</CardDescription>
                  </div>
                  <Sparkles className="mt-1 size-5 text-muted-foreground" />
                </div>
              </CardHeader>
              <CardContent>
                <form className="grid gap-5" onSubmit={handleGenerate}>
                  <label className="grid gap-2">
                    <span className="text-sm font-medium">
                      Tema / kata kunci
                    </span>
                    <textarea
                      className="min-h-28 resize-none rounded-lg border border-input bg-background px-3 py-2 text-sm shadow-xs transition-colors outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
                      placeholder="Contoh: pendidikan, cinta, persahabatan, teknologi"
                      value={tema}
                      onChange={(event) => setTema(event.target.value)}
                    />
                  </label>

                  <div className="grid gap-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Contoh tema</span>
                      <span className="text-xs text-muted-foreground">
                        klik untuk pakai cepat
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {EXAMPLE_THEMES.map((item) => (
                        <Button
                          key={item}
                          size="sm"
                          type="button"
                          variant={tema === item ? "default" : "outline"}
                          onClick={() => setTema(item)}
                        >
                          {item}
                        </Button>
                      ))}
                    </div>
                  </div>

                  {error ? (
                    <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                      {error}
                    </div>
                  ) : null}

                  <Button disabled={!canGenerate} size="lg" type="submit">
                    {isLoading ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : (
                      <Sparkles className="size-4" />
                    )}
                    {isLoading ? "Membuat Pantun..." : "Generate Pantun"}
                  </Button>
                </form>
              </CardContent>
            </Card>

            <Card className="shadow-sm">
              <CardHeader className="border-b">
                <div className="flex items-start justify-between gap-4">
                  <div className="grid gap-1">
                    <CardTitle className="text-base">Parameter</CardTitle>
                    <CardDescription>
                      Kontrol kreativitas dan panjang output.
                    </CardDescription>
                  </div>
                  <Button
                    size="sm"
                    type="button"
                    variant="ghost"
                    onClick={resetSettings}
                  >
                    <RotateCcw className="size-4" />
                    Reset
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="grid gap-5">
                <SliderField
                  helper="Lebih tinggi berarti output lebih variatif."
                  label="Temperature"
                  max={1.5}
                  min={0.1}
                  step={0.1}
                  value={temperature}
                  onChange={setTemperature}
                />
                <SliderField
                  helper="Batasi token kandidat terbaik."
                  label="Top-K"
                  max={100}
                  min={1}
                  step={1}
                  value={topK}
                  onChange={setTopK}
                />
                <SliderField
                  helper="Nucleus sampling agar tetap natural."
                  label="Top-P"
                  max={1}
                  min={0.1}
                  step={0.05}
                  value={topP}
                  onChange={setTopP}
                />
                <SliderField
                  helper="Panjang maksimal teks yang dihasilkan."
                  label="Max New Tokens"
                  max={150}
                  min={20}
                  step={5}
                  value={maxNewTokens}
                  onChange={setMaxNewTokens}
                />
              </CardContent>
            </Card>
          </div>

          <Card className="min-h-[calc(100svh-8.5rem)] shadow-sm lg:sticky lg:top-24">
            <CardHeader className="border-b">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="grid gap-1">
                  <CardTitle className="text-xl">Hasil pantun</CardTitle>
                  <CardDescription>
                    Dengarkan, salin, atau generate ulang sampai pas.
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button
                    disabled={!pantun.trim()}
                    size="sm"
                    type="button"
                    variant="outline"
                    onClick={handleCopy}
                  >
                    {hasCopied ? (
                      <Check className="size-4" />
                    ) : (
                      <Copy className="size-4" />
                    )}
                    {hasCopied ? "Tersalin" : "Salin"}
                  </Button>
                  <Button
                    disabled={!pantun.trim()}
                    size="sm"
                    type="button"
                    onClick={() => speakPantun(pantun)}
                  >
                    <Volume2 className="size-4" />
                    Baca
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="grid gap-4">
              <div className="rounded-xl border bg-background p-4 sm:p-6">
                {pantunLines.length > 0 ? (
                  <div className="grid gap-3">
                    {pantunLines.map((line, index) => (
                      <div
                        className="grid grid-cols-[2rem_1fr] items-start gap-3 rounded-lg border bg-muted/25 p-3"
                        key={`${line}-${index}`}
                      >
                        <span className="flex size-8 items-center justify-center rounded-md bg-background font-mono text-xs text-muted-foreground">
                          {index + 1}
                        </span>
                        <p className="pt-1 text-lg leading-8">{line}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="grid min-h-[430px] place-items-center">
                    <div className="mx-auto grid max-w-sm justify-items-center gap-3 text-center">
                      <div className="flex size-14 items-center justify-center rounded-2xl bg-muted">
                        <SlidersHorizontal className="size-6 text-muted-foreground" />
                      </div>
                      <div className="grid gap-1">
                        <p className="font-medium">Pantun belum dibuat.</p>
                        <p className="text-sm leading-6 text-muted-foreground">
                          Masukkan tema di panel kiri, pilih contoh tema jika
                          perlu, lalu klik Generate Pantun.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="grid gap-3 rounded-xl border bg-muted/30 p-4 sm:grid-cols-3">
                <div className="grid gap-1">
                  <span className="text-xs text-muted-foreground">Tema</span>
                  <span className="truncate text-sm font-medium">
                    {tema.trim() || "-"}
                  </span>
                </div>
                <div className="grid gap-1">
                  <span className="text-xs text-muted-foreground">
                    Parameter
                  </span>
                  <span className="text-sm font-medium">
                    T {temperature} / K {topK} / P {topP}
                  </span>
                </div>
                <div className="grid gap-1">
                  <span className="text-xs text-muted-foreground">Panjang</span>
                  <span className="text-sm font-medium">
                    {maxNewTokens} tokens
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </main>
  )
}

export default App
