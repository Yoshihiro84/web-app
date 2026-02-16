const CATEGORY_ORDER = ["論文", "学会発表", "受賞", "プロジェクト", "GitHub"];

function parseDateValue(value) {
  const [year, month = "01"] = value.split("-");
  return new Date(Number(year), Number(month) - 1, 1).getTime();
}

function sortByNewest(items) {
  return [...items].sort((a, b) => parseDateValue(b.date) - parseDateValue(a.date));
}

function createAchievementCard(item) {
  const authors = item.coauthors && item.coauthors.length > 0 ? item.coauthors.join(", ") : "なし";
  const safeLink = item.link && item.link !== "#" ? item.link : null;
  const linkPart = safeLink
    ? `<a href="${safeLink}" target="_blank" rel="noreferrer">リンク</a>`
    : "リンク未設定";

  return `
    <article class="achievement-item">
      <p class="meta">${item.category} | ${item.date}</p>
      <h3>${item.title}</h3>
      <p>${item.summary}</p>
      <p><strong>共同著者:</strong> ${authors}</p>
      <p>${linkPart}</p>
    </article>
  `;
}

async function loadAchievements() {
  const response = await fetch("data/achievements.json");
  if (!response.ok) {
    throw new Error("実績データの読み込みに失敗しました。");
  }
  const data = await response.json();
  return sortByNewest(data);
}

function renderHighlights(items) {
  const root = document.getElementById("highlights");
  if (!root) return;

  const html = items.slice(0, 3).map(createAchievementCard).join("");
  root.innerHTML = html || "<p>表示できる実績がありません。</p>";
}

function renderPublications(items) {
  const root = document.getElementById("publications-root");
  if (!root) return;

  const blocks = CATEGORY_ORDER.map((category) => {
    const entries = items.filter((item) => item.category === category);
    if (entries.length === 0) {
      return `
        <section class="achievement-block">
          <h2>${category}</h2>
          <p class="note">まだ実績がありません。</p>
        </section>
      `;
    }

    const listHtml = entries.map((item) => `<li>${createAchievementCard(item)}</li>`).join("");
    return `
      <section class="achievement-block">
        <h2>${category}</h2>
        <ul class="achievement-list">${listHtml}</ul>
      </section>
    `;
  }).join("");

  root.innerHTML = blocks;
}

async function main() {
  const page = document.body.dataset.page;
  if (!page) return;

  try {
    const items = await loadAchievements();
    if (page === "home") {
      renderHighlights(items);
    } else if (page === "publications") {
      renderPublications(items);
    }
  } catch (error) {
    const message = `<p class="note">${error.message}</p>`;
    const highlights = document.getElementById("highlights");
    const publications = document.getElementById("publications-root");
    if (highlights) highlights.innerHTML = message;
    if (publications) publications.innerHTML = message;
  }
}

main();
