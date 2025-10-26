import express from "express";
import { spawn } from "child_process";

const app = express();

// Python botni ishga tushiramiz
const bot = spawn("python", ["main.py"]);

bot.stdout.on("data", (data) => {
  console.log(`BOT: ${data}`);
});

bot.stderr.on("data", (data) => {
  console.error(`ERROR: ${data}`);
});

bot.on("close", (code) => {
  console.log(`Bot process tugadi (kod: ${code})`);
});

// Render “alive” bo‘lishi uchun minimal server
app.get("/", (req, res) => {
  res.send("🤖 HISOBOT24 bot ishlayapti!");
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => {
  console.log(`Server ${PORT}-portda ishlayapti`);
});
