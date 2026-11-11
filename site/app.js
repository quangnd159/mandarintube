// MandarinTube: a static site. All personal state stays in this browser.
const LEVELS = [
  { id: 1, zh: "初", vi: "Mới bắt đầu", en: "Beginner", hsk: "HSK 1–2" },
  { id: 2, zh: "进", vi: "Tiền trung cấp", en: "Lower intermediate", hsk: "HSK 3" },
  { id: 3, zh: "中", vi: "Trung cấp", en: "Intermediate", hsk: "HSK 4–5" },
  { id: 4, zh: "高", vi: "Nâng cao", en: "Advanced", hsk: "HSK 6+" },
];
const LENGTHS = [
  { id: "any", test: () => true },
  { id: "short", test: (d) => d < 600 },
  { id: "mid", test: (d) => d >= 600 && d < 1800 },
  { id: "long", test: (d) => d >= 1800 },
];
const PAGE = 24;
const QUANG = "https://www.dqnotes.com/";
const REPO = "https://github.com/quangnd159/mandarintube";

const T = {
  vi: {
    skip: "Chuyển đến nội dung", navHome: "Trang chủ", navChannels: "Kênh", navSaved: "Đã lưu", navMethod: "Cách chọn",
    loading: "Đang tải video…",
    loadFailed: (m) => `Không tải được danh sách video (${m}).`, loadFix: "Hãy kiểm tra kết nối rồi tải lại trang.",
    intro: (v, c) => `${v} video luyện nghe tiếng Trung từ ${c} kênh`,
    introSub: (p) => `Dựa trên gợi ý của ${p} người học và đã loại các kênh do AI tạo. Chọn trình độ của bạn.`,
    levelGroup: "Trình độ của bạn", lengthGroup: "Độ dài video",
    any: "Mọi độ dài", short: "Dưới 10 phút", mid: "10–30 phút", long: "Trên 30 phút",
    search: "Tìm theo tiêu đề hoặc kênh", count: (n) => `${n} video`,
    noMatch: "Không có video nào khớp với bộ lọc này.", noMatchFix: "Hãy thử độ dài hoặc trình độ khác.", reset: "Xóa bộ lọc",
    views: (n) => `${n} lượt xem`,
    notFound: "Video này không có trong thư viện.", goHome: "Về trang chủ",
    like: "Thích", liked: "Đã thích", later: "Xem sau", savedLater: "Đã lưu xem sau", openYt: "Mở trên YouTube",
    why: "Vì sao video này có ở đây", upNext: "Xem tiếp",
    autoplay: "Tự phát tiếp", inSecs: (n) => `sau ${n} giây`, nextLabel: "Tiếp theo",
    playNow: "Phát ngay", cancel: "Hủy", cantPlay: "Video này không phát được ở đây.",
    levelLabelled: (l) => `Trình độ: ${l}, theo nhãn của giáo viên.`,
    levelEstimated: (l) => `Trình độ ${l} là ước tính dựa trên các video khác của kênh.`,
    recommended: (p, t, span) => `Được ${p} người giới thiệu trong ${t} chủ đề trên Reddit${span}.`,
    span: (a, b) => `, từ ${a} đến ${b}`, spanOne: (a) => `, năm ${a}`,
    fans: (n) => `${n}% người bình luận được lấy mẫu cũng bình luận ở các kênh gốc.`,
    seed: "Một trong các kênh gốc mà trang này dựa vào.",
    handAdded: "Được thêm vào nhờ có nhiều người xem chung với các kênh gốc.",
    channelsTitle: "Xếp hạng các kênh",
    channelsLead: "Xếp theo số người học liên tục giới thiệu và số người xem chung với các kênh gốc.",
    seeHow: "Xem cách chọn",
    countHere: (n) => `${n} video ở đây`, mostly: (l) => `, chủ yếu ${l}`,
    speed: (n) => `Nói khoảng ${n} chữ mỗi phút.`,
    channelMissing: "Kênh này không có trong thư viện.", seeChannels: "Xem tất cả các kênh",
    redditYear: (y) => `Bình luận trên Reddit năm ${y}`,
    hide: "Ẩn khỏi trang chủ", hidden: "Đã ẩn khỏi trang chủ",
    savedTitle: "Đã lưu", savedLead: "Chỉ lưu trong trình duyệt này. Trang không có tài khoản nên dữ liệu không theo bạn sang thiết bị khác.",
    tabLiked: "Đã thích", tabLater: "Xem sau", tabHistory: "Lịch sử",
    clearHistory: "Xóa lịch sử", clearConfirm: "Bấm lần nữa để xóa",
    emptyLiked: ["Chưa thích video nào.", "Bấm Thích dưới một video để lưu ở đây. Lượt thích cũng giúp trang chủ hợp với bạn hơn."],
    emptyLater: ["Chưa có video nào để xem sau.", "Bấm Xem sau dưới một video để lưu ở đây."],
    emptyHistory: ["Chưa có lịch sử.", "Những video bạn mở sẽ hiện ở đây."],
    browse: "Xem video",
    mTitle: "Cách chọn",
    mLead: "YouTube gợi ý thứ giữ bạn xem lâu hơn. Trang này cố gắng gợi ý thứ thực sự giúp người ta học, dựa trên những bằng chứng khó làm giả.",
    mFrom: "Các kênh đến từ đâu",
    mFromBody: (rows, first, seeds) => `Trang đã đọc ${rows} bình luận và bài đăng từ các cộng đồng học tiếng Trung trên Reddit, từ năm ${first} đến nay, để tìm những kênh được nhắc tới. Danh sách còn được bổ sung từ tìm kiếm trên YouTube và danh sách của Hacking Chinese, dù chỉ riêng việc được tìm thấy thì chưa đủ để lên trang. Bốn kênh gốc do chủ trang yêu thích là: ${seeds}.`,
    mRank: "Các kênh được xếp hạng thế nào",
    mRankLead: "Hai tín hiệu độc lập được kết hợp:",
    mRank1Title: "Người học liên tục giới thiệu.", mRank1: "Đếm số người khác nhau chứ không đếm số lần nhắc, và coi trọng kênh được giới thiệu qua nhiều chủ đề, nhiều năm. Một người nhắc nhiều lần chỉ tính một. Bình luận bị downvote, bài chỉ đăng link và người tự quảng bá kênh của mình đều không được tính.",
    mRank2Title: "Người xem chung.",
    mGate: "Ngoài bốn kênh gốc, một kênh phải có ít nhất 3 người giới thiệu độc lập hoặc 5 người xem chung thì mới được đưa vào. Trong mỗi kênh, video được sắp theo lượt xem so với mức thường thấy ở độ tuổi của video đó, nên bài hay nhất của một giáo viên nhỏ vẫn có thể vượt bài trung bình của một kênh lớn.",
    mListen: "Chỉ có video luyện nghe",
    mListenBody: "Trang này dành cho việc nghe tiếng Trung. Danh sách từ vựng, đề thi, bài ngữ pháp và phát âm bị lược bỏ, kể cả khi đến từ kênh hay, trừ khi tiêu đề cho thấy đó là câu chuyện, podcast hay hội thoại. Video chỉ dành cho hội viên và Shorts cũng bị bỏ, cùng với video mà YouTube nhận diện là nói bằng tiếng Anh, nên đôi khi một video hay có thể bị loại nhầm.",
    mAi: "Giữ các kênh do AI tạo ở ngoài",
    mTitles: "Tiêu đề tiếng Việt",
    mTitlesBody: "Claude, một trợ lý AI, đã dịch và rút gọn tiêu đề video sang tiếng Việt, bỏ các nhãn trình độ và từ khóa mà trang đã hiển thị ở chỗ khác. Một số tiêu đề có thể chưa chính xác, và chưa có người nào đọc lại toàn bộ. Tiêu đề gốc luôn nằm dưới video.",
    mLevels: "Trình độ được xác định thế nào",
    credit: "Xem các dự án khác của Quang tại dqnotes.com", sourceCode: "Mã nguồn trên GitHub",
    mBuild: "Làm trang này cho ngôn ngữ khác",
    mBuildBody: "Đưa câu lệnh này cho một trợ lý AI viết mã, rồi điền vào phần trong ngoặc vuông.",
    copy: "Sao chép câu lệnh", copied: "Đã sao chép", copySelect: "Hãy nhấn Cmd/Ctrl+C để sao chép",
    mPrivacy: "Những gì được lưu về bạn",
    mPrivacyBody: "Lượt thích, lịch sử và trình độ của bạn chỉ nằm trong trình duyệt này. Trang không có tài khoản và không có công cụ phân tích. Video phát qua trình phát chế độ riêng tư của YouTube, và điều khoản của YouTube áp dụng khi video bắt đầu chạy.",
    mThumbs: (d) => `Ảnh thu nhỏ là khung hình giữa video, không phải ảnh do người đăng thiết kế. Cập nhật lần cuối: ${d}.`,
  },
  en: {
    skip: "Skip to content", navHome: "Home", navChannels: "Channels", navSaved: "Saved", navMethod: "How it’s chosen",
    loading: "Loading videos…",
    loadFailed: (m) => `The video list didn’t load (${m}).`, loadFix: "Check your connection and reload the page.",
    intro: (v, c) => `${v} Mandarin listening videos from ${c} channels`,
    introSub: (p) => `Based on what ${p} learners recommended, with AI-generated channels removed. Pick your level.`,
    levelGroup: "Your level", lengthGroup: "Video length",
    any: "Any length", short: "Under 10 min", mid: "10–30 min", long: "Over 30 min",
    search: "Search titles and channels", count: (n) => `${n} videos`,
    noMatch: "No videos match these filters.", noMatchFix: "Try another length or level.", reset: "Clear filters",
    views: (n) => `${n} views`,
    notFound: "This video isn’t in the library.", goHome: "Go to the home page",
    like: "Like", liked: "Liked", later: "Watch later", savedLater: "Saved for later", openYt: "Open on YouTube",
    why: "Why this is here", upNext: "Up next",
    autoplay: "Autoplay", inSecs: (n) => `in ${n}s`, nextLabel: "Up next",
    playNow: "Play now", cancel: "Cancel", cantPlay: "This video can’t be played here.",
    levelLabelled: (l) => `Level: ${l}, as labelled by the teacher.`,
    levelEstimated: (l) => `The ${l} level is an estimate based on this channel’s other videos.`,
    recommended: (p, t, span) => `Recommended by ${p} people in ${t} Reddit threads${span}.`,
    span: (a, b) => ` from ${a} to ${b}`, spanOne: (a) => ` in ${a}`,
    fans: (n) => `${n}% of its sampled commenters also comment on the starting channels.`,
    seed: "One of the starting channels this site is built around.",
    handAdded: "Included because it shares many viewers with the starting channels.",
    channelsTitle: "Channels, best first",
    channelsLead: "Ranked by how many learners keep recommending each channel and how many viewers it shares with the starting channels.",
    seeHow: "See how it’s chosen",
    countHere: (n) => `${n} videos here`, mostly: (l) => `, mostly ${l}`,
    speed: (n) => `Speaks about ${n} characters a minute.`,
    channelMissing: "This channel isn’t in the library.", seeChannels: "See all channels",
    redditYear: (y) => `Reddit comment from ${y}`,
    hide: "Hide from home", hidden: "Hidden from home",
    savedTitle: "Saved", savedLead: "Kept in this browser only. There’s no account, so it won’t follow you to another device.",
    tabLiked: "Liked", tabLater: "Watch later", tabHistory: "History",
    clearHistory: "Clear history", clearConfirm: "Press again to clear",
    emptyLiked: ["Nothing liked yet.", "Press Like under a video to keep it here. Likes also shape your home page."],
    emptyLater: ["Nothing saved for later.", "Press Watch later under a video to keep it here."],
    emptyHistory: ["No history yet.", "Videos you open appear here."],
    browse: "Browse videos",
    mTitle: "How it’s chosen",
    mLead: "YouTube recommends what keeps you watching. This site tries to recommend what actually helped people learn, using evidence that’s hard to fake.",
    mFrom: "Where the channels come from",
    mFromBody: (rows, first, seeds) => `The site read ${rows} comments and posts from Mandarin-learning communities on Reddit, going back to ${first}, looking for channels people mention. YouTube search and Hacking Chinese’s list added more candidates, though being found isn’t enough to get listed. The four starting channels are the site owner’s favourites: ${seeds}.`,
    mRank: "How channels are ranked",
    mRankLead: "Two independent signals, combined:",
    mRank1Title: "Learners who keep recommending it.", mRank1: "It counts different people rather than mentions, and gives more weight to channels recommended across many threads and years. One person repeating themselves counts once. Downvoted comments, bare link posts and people promoting their own channel don’t count.",
    mRank2Title: "Shared viewers.",
    mGate: "Apart from the four starting channels, a channel needs at least 3 independent recommenders or 5 shared viewers to be listed. Within a channel, videos are ordered by their views compared with what’s typical for their age, so a small teacher’s best lesson can beat a big channel’s average one.",
    mListen: "Listening videos only",
    mListenBody: "This site is for hearing Mandarin. Vocabulary lists, exam papers, grammar and pronunciation lessons are left out, even from good channels, unless the title shows it’s a story, podcast or conversation. Members-only videos and Shorts are left out too, along with videos YouTube detects as spoken in English, so a good one is occasionally removed by mistake.",
    mAi: "Keeping AI-generated channels out",
    mTitles: "Vietnamese titles",
    mTitlesBody: "Claude, an AI assistant, translated and shortened the video titles into Vietnamese, dropping level labels and keywords the site shows elsewhere. Some may be inaccurate, and no person has read them all. The original title is always under the video.",
    mLevels: "How levels work",
    credit: "See other stuff by Quang at dqnotes.com", sourceCode: "Source code on GitHub",
    mBuild: "Make this for another language",
    mBuildBody: "Give this prompt to an AI coding agent, and fill in the square brackets.",
    copy: "Copy prompt", copied: "Copied", copySelect: "Press Cmd/Ctrl+C to copy",
    mPrivacy: "What’s stored about you",
    mPrivacyBody: "Likes, history and your level stay in this browser. There’s no account and no analytics on this site. Videos play through YouTube’s privacy-enhanced player, and YouTube’s terms apply once one starts.",
    mThumbs: (d) => `Thumbnails are frames from the middle of each video, not the thumbnail the uploader designed. Last updated ${d}.`,
  },
};

/* ---------- Saved state ---------- */
const store = {
  read(key, fallback) {
    try {
      const raw = localStorage.getItem("mt." + key);
      return raw === null ? fallback : JSON.parse(raw);
    } catch { return fallback; }
  },
  write(key, value) {
    try { localStorage.setItem("mt." + key, JSON.stringify(value)); } catch { /* private mode: state lasts for this page only */ }
  },
};
const state = {
  lang: store.read("lang", "vi") === "en" ? "en" : "vi",
  level: store.read("level", null),
  length: store.read("length", "any"),
  liked: store.read("liked", []),
  later: store.read("later", []),
  history: store.read("history", []),
  autoplay: store.read("autoplay", true) !== false,
  hidden: store.read("hidden", []), // Channel IDs, because list positions change on every rebuild.
  query: "",
};
if (!LENGTHS.some((l) => l.id === state.length)) state.length = "any";
// New order each visit, stable within it, so the home page doesn't feel frozen.
const sessionSeed = Math.random();

let DATA, VIDEOS, BY_ID;
let shownNow = 0; // Cards currently rendered, kept so Back can restore the same position.
const feedCache = new Map(); // Holds the order steady while someone goes to a video and back.
const main = document.getElementById("main");
const t = () => T[state.lang];
const levelName = (l) => l[state.lang];
const locale = () => (state.lang === "vi" ? "vi-VN" : "en-US");

/* ---------- Helpers ---------- */
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmtDur = (s) => {
  if (!s) return "";
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), x = String(s % 60).padStart(2, "0");
  return h ? `${h}:${String(m).padStart(2, "0")}:${x}` : `${m}:${x}`;
};
const fmtInt = (n) => Number(n).toLocaleString(locale());
const fmtCompact = (n) => new Intl.NumberFormat(locale(), { notation: "compact", maximumFractionDigits: 1 }).format(n || 0);
const titleOf = (v) => (state.lang === "vi" && v.vt) || v.t;
const levelOf = (id) => LEVELS.find((l) => l.id === id);
const channelHref = (c) => `/?c=${encodeURIComponent(c.key)}`;
const hash01 = (str, seed) => {
  let h = 2166136261 ^ Math.floor(seed * 1e9);
  for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); }
  return (h >>> 0) / 4294967296;
};
// Search ignores case and diacritics, so "hoc" finds "học".
const fold = (s) => s.normalize("NFD").replace(/\p{M}/gu, "").replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase();
const lengthBucket = (d) => (d < 600 ? "short" : d < 1800 ? "mid" : "long");

/* ---------- Recommendations: plain arithmetic on what you did here ---------- */
function affinity() {
  const byChannel = new Map(), byLength = new Map();
  const add = (id, weight) => {
    const v = BY_ID.get(id);
    if (!v) return;
    byChannel.set(v.c, (byChannel.get(v.c) || 0) + weight);
    const b = lengthBucket(v.d);
    byLength.set(b, (byLength.get(b) || 0) + weight);
  };
  state.history.slice(0, 40).forEach((h, i) => add(h.id, 1 / (1 + i / 8)));
  state.liked.forEach((id) => add(id, 3));
  state.later.forEach((id) => add(id, 1));
  const norm = (m) => { const top = Math.max(1, ...m.values()); return (k) => (m.get(k) || 0) / top; };
  return { channel: norm(byChannel), length: norm(byLength) };
}

function ranked(videos, { personal = true } = {}) {
  const aff = affinity();
  const seen = new Set(state.history.map((h) => h.id));
  const scored = videos.map((v) => {
    let s = v.s + 0.25 * hash01(v.id, sessionSeed);
    if (personal) s += 0.45 * aff.channel(v.c) + 0.15 * aff.length(lengthBucket(v.d));
    if (seen.has(v.id)) s -= 1;
    return { v, s };
  }).sort((a, b) => b.s - a.s);

  // Spread channels out: each pick from a channel discounts its next one.
  const queues = new Map();
  for (const x of scored) {
    if (!queues.has(x.v.c)) queues.set(x.v.c, []);
    queues.get(x.v.c).push(x);
  }
  const heads = [...queues.values()].map((q) => ({ q, i: 0, taken: 0 }));
  const out = [];
  while (heads.length) {
    let best = 0, bestScore = -Infinity;
    for (let h = 0; h < heads.length; h++) {
      const e = heads[h].q[heads[h].i].s - 0.12 * heads[h].taken;
      if (e > bestScore) { bestScore = e; best = h; }
    }
    const head = heads[best];
    out.push(head.q[head.i].v);
    head.i++; head.taken++;
    if (head.i >= head.q.length) heads.splice(best, 1);
  }
  return out;
}

const isHidden = (v) => state.hidden.includes(DATA.channels[v.c].id);
function matchesFilters(v, q) {
  if (isHidden(v)) return false;
  if (state.level && v.l !== state.level) return false;
  if (!LENGTHS.find((l) => l.id === state.length).test(v.d)) return false;
  return !q || v.q.includes(q);
}
function currentFeed() {
  const key = [state.level, state.length, state.query, state.hidden.join()].join("|");
  if (!feedCache.has(key)) {
    const q = fold(state.query);
    feedCache.set(key, ranked(VIDEOS.filter((v) => matchesFilters(v, q))));
  }
  return feedCache.get(key);
}

/* ---------- Pieces ---------- */
function thumbImg(id) {
  // hq2 is a frame YouTube samples from the middle of the video, not the uploader's chosen thumbnail.
  return `<img src="https://i.ytimg.com/vi/${id}/hq2.jpg" data-id="${id}" alt="" loading="lazy" decoding="async" width="480" height="270">`;
}
function metaLine(v) {
  const c = DATA.channels[v.c], lvl = levelOf(v.l);
  const bits = [`<a href="${channelHref(c)}" data-link>${esc(c.name)}</a>`];
  if (lvl) bits.push(`<span class="lvl">${esc(levelName(lvl))}</span>`);
  if (v.v) bits.push(`<span>${esc(t().views(fmtCompact(v.v)))}</span>`);
  return `<div class="meta">${bits.join("")}</div>`;
}
function card(v) {
  return `<article class="card">
    <a href="/?v=${v.id}" data-link>
      <div class="thumb">${thumbImg(v.id)}<span class="dur">${fmtDur(v.d)}</span></div>
      <h2 class="card-title">${esc(titleOf(v))}</h2>
    </a>${metaLine(v)}</article>`;
}
function evidenceSentence(c) {
  const L = t(), parts = [];
  if (c.people) {
    const span = c.first && c.last && c.first !== c.last ? L.span(c.first, c.last) : c.first ? L.spanOne(c.first) : "";
    parts.push(L.recommended(fmtInt(c.people), fmtInt(c.threads), span));
  }
  if (c.fanShare && !c.seed) parts.push(L.fans(Math.max(1, Math.round(c.fanShare * 100))));
  if (c.seed) parts.push(L.seed);
  return parts.join(" ") || L.handAdded;
}
function bindPager(list, container, initial = PAGE) {
  let shown = 0;
  const sentinel = document.createElement("div");
  sentinel.className = "sentinel";
  container.after(sentinel);
  const more = (n = PAGE) => {
    container.insertAdjacentHTML("beforeend", list.slice(shown, shown + n).map(card).join(""));
    shown += n;
    shownNow = Math.min(shown, list.length);
    if (shown >= list.length) { io.disconnect(); sentinel.remove(); }
  };
  const io = new IntersectionObserver((entries) => { if (entries.some((e) => e.isIntersecting)) more(); }, { rootMargin: "800px" });
  if (!list.length) { sentinel.remove(); return; }
  io.observe(sentinel);
  more(Math.max(PAGE, initial));
}
const emptyBlock = (a, b, action = "") => `<div class="empty"><p>${esc(a)}</p><p>${esc(b)}</p>${action}</div>`;

/* ---------- Views ---------- */
function viewHome(restore) {
  const L = t();
  document.title = "MandarinTube";
  main.innerHTML = `
    <h1 class="intro">${esc(L.intro(fmtInt(DATA.stats.videos), DATA.channels.length))}</h1>
    <p class="intro-sub">${esc(L.introSub(fmtInt(DATA.stats.people)))}</p>
    <div class="levels" role="group" aria-label="${esc(L.levelGroup)}">
      ${LEVELS.map((l) => `<button class="level" type="button" data-level="${l.id}" aria-pressed="${state.level === l.id}">
        <span class="cell"><span class="zh" lang="zh-Hans">${l.zh}</span></span>
        <span class="level-name">${esc(levelName(l))}</span><span class="level-hsk">${l.hsk}</span>
      </button>`).join("")}
    </div>
    <div class="filters">
      <div class="chips" role="group" aria-label="${esc(L.lengthGroup)}">
        ${LENGTHS.map((l) => `<button class="chip" type="button" data-length="${l.id}" aria-pressed="${state.length === l.id}">${esc(L[l.id])}</button>`).join("")}
      </div>
      <input class="search" type="search" placeholder="${esc(L.search)}" aria-label="${esc(L.search)}" value="${esc(state.query)}" autocomplete="off" autocorrect="off" spellcheck="false" enterkeyhint="search">
    </div>
    <p class="result-note" id="count" aria-live="polite"></p>
    <div id="feed"></div>`;
  renderFeed(restore?.shown);
  main.querySelector(".search").addEventListener("input", (e) => { state.query = e.target.value.trim(); renderFeed(); });
}
function renderFeed(initial) {
  const holder = main.querySelector("#feed");
  if (!holder) return;
  main.querySelectorAll(".sentinel").forEach((s) => s.remove());
  const L = t(), list = currentFeed();
  // The headline already gives the full total, so this only speaks up once a filter narrows it.
  const filtered = state.level || state.length !== "any" || state.query;
  main.querySelector("#count").textContent = filtered ? L.count(fmtInt(list.length)) : "";
  if (!list.length) {
    holder.innerHTML = emptyBlock(L.noMatch, L.noMatchFix, `<button class="chip" type="button" data-reset>${esc(L.reset)}</button>`);
    return;
  }
  holder.innerHTML = `<div class="grid" id="grid"></div>`;
  bindPager(list, holder.querySelector("#grid"), initial);
}

function toggleLabel(key, on) {
  const L = t();
  return key === "liked" ? (on ? L.liked : L.like) : (on ? L.savedLater : L.later);
}
function viewWatch(id) {
  const L = t(), v = BY_ID.get(id);
  if (!v) {
    document.title = "MandarinTube";
    main.innerHTML = emptyBlock(L.notFound, "", `<a class="chip" href="/" data-link>${esc(L.goHome)}</a>`);
    return;
  }
  document.title = `${titleOf(v)} | MandarinTube`;
  state.history = [{ id, t: Date.now() }, ...state.history.filter((h) => h.id !== id)].slice(0, 500);
  store.write("history", state.history);
  const same = ranked(VIDEOS.filter((x) => x.id !== id && x.c === v.c && (!v.l || x.l === v.l)), { personal: false }).slice(0, 4);
  const others = ranked(VIDEOS.filter((x) => x.id !== id && x.c !== v.c && x.l === v.l && !isHidden(x))).slice(0, 8);
  const upNext = [...same, ...others];
  // Autoplay picks the first one not watched yet, so a run of videos never circles back.
  const seen = new Set(state.history.map((h) => h.id));
  player.nextId = (upNext.find((n) => !seen.has(n.id)) || upNext[0])?.id || null;

  // Going from one video to the next keeps the same iframe and tells it to load the new one.
  // A fresh iframe would need a new tap before it may play with sound, especially on phones.
  const live = player.ready && player.frame?.isConnected && main.querySelector(".watch .player");
  if (live) {
    player.load(id);
    player.frame.title = v.t;
    main.querySelector(".watch-info").innerHTML = watchInfo(v);
    main.querySelector(".next").innerHTML = upNextList(upNext);
    return;
  }
  const params = new URLSearchParams({ rel: "0", modestbranding: "1", hl: state.lang, cc_lang_pref: "zh-Hans", autoplay: "1", playsinline: "1", enablejsapi: "1", origin: location.origin });
  main.innerHTML = `<div class="watch">
    <div class="watch-main">
      <div class="player"><iframe src="${YT_ORIGIN}/embed/${id}?${params}" title="${esc(v.t)}" referrerpolicy="strict-origin-when-cross-origin" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen></iframe><div class="endcard" hidden></div></div>
      <div class="watch-info">${watchInfo(v)}</div>
    </div>
    <aside class="next" aria-label="${esc(L.upNext)}">${upNextList(upNext)}</aside>
  </div>`;
  player.attach(main.querySelector(".player iframe"), id);
}
function watchInfo(v) {
  const L = t(), c = DATA.channels[v.c], lvl = levelOf(v.l), id = v.id;
  const levelNote = lvl ? (v.ls ? L.levelLabelled(levelName(lvl).toLowerCase()) : L.levelEstimated(levelName(lvl).toLowerCase())) : "";
  const liked = state.liked.includes(id), later = state.later.includes(id);
  return `<h1>${esc(titleOf(v))}</h1>
      <p class="orig" lang="und"${titleOf(v) === v.t ? " hidden" : ""}>${esc(v.t)}</p>
      <div class="meta"><a href="${channelHref(c)}" data-link>${esc(c.name)}</a>${v.v ? `<span>${esc(L.views(fmtCompact(v.v)))}</span>` : ""}<span>${fmtDur(v.d)}</span></div>
      <div class="actions">
        <button class="chip" type="button" data-toggle="liked" data-id="${id}" aria-pressed="${liked}">${esc(toggleLabel("liked", liked))}</button>
        <button class="chip" type="button" data-toggle="later" data-id="${id}" aria-pressed="${later}">${esc(toggleLabel("later", later))}</button>
        <a class="chip" href="https://www.youtube.com/watch?v=${id}" target="_blank" rel="noopener">${esc(L.openYt)}</a>
      </div>
      <section class="evidence">
        <h2>${esc(L.why)}</h2>
        <p>${esc(evidenceSentence(c))} ${esc(levelNote)}</p>
      </section>`;
}
function upNextList(list) {
  const L = t();
  return `<div class="next-head"><h2>${esc(L.upNext)}</h2>
      <label class="switch"><input type="checkbox" data-autoplay${state.autoplay ? " checked" : ""}><span>${esc(L.autoplay)}</span></label></div>
      ${list.map((n) => `<a class="next-item" href="/?v=${n.id}" data-link>
        <div class="thumb">${thumbImg(n.id)}<span class="dur">${fmtDur(n.d)}</span></div>
        <div><div class="card-title" data-vid="${n.id}">${esc(titleOf(n))}</div><div class="meta"><span>${esc(DATA.channels[n.c].name)}</span></div></div>
      </a>`).join("")}`;
}

/* ---------- Player: YouTube's embed speaks postMessage, so no extra script loads ---------- */
const YT_ORIGIN = "https://www.youtube-nocookie.com";
const COUNTDOWN = 8; // Seconds: long enough to stop it, short enough to keep listening.
const player = {
  frame: null, ready: false, id: null, nextId: null, lastState: null, hello: 0, tick: 0,
  send(msg) { this.frame?.contentWindow?.postMessage(JSON.stringify({ id: 1, channel: "widget", ...msg }), YT_ORIGIN); },
  command(func, args = []) { this.send({ event: "command", func, args }); },
  attach(frame, id) {
    this.stopCountdown();
    Object.assign(this, { frame, ready: false, id, lastState: null });
    // The embed only starts reporting once it hears "listening", and it may not be ready for the first few.
    clearInterval(this.hello);
    const greet = () => { if (this.ready || !frame.isConnected) clearInterval(this.hello); else this.send({ event: "listening" }); };
    frame.addEventListener("load", greet);
    this.hello = setInterval(greet, 250);
  },
  load(id) {
    this.stopCountdown();
    this.id = id; this.lastState = null;
    this.command("loadVideoById", [id, 0]);
  },
  stopCountdown() {
    clearInterval(this.tick); this.tick = 0;
    const card = main.querySelector(".endcard");
    if (card) { card.hidden = true; card.innerHTML = ""; }
  },
  // Shown over the player when a video ends or can't play. It counts down only with autoplay on.
  showEndcard(reason) {
    const card = main.querySelector(".endcard"), next = BY_ID.get(this.nextId);
    if (!card || !next) return;
    const L = t(), href = `/?v=${next.id}`, counting = state.autoplay;
    let left = COUNTDOWN;
    card.innerHTML = `<div class="endcard-inner">
      <a class="endcard-thumb" href="${href}" data-link tabindex="-1" aria-hidden="true"><div class="thumb">${thumbImg(next.id)}<span class="dur">${fmtDur(next.d)}</span></div></a>
      <div class="endcard-body">
        ${reason === "error" ? `<p class="endcard-note">${esc(L.cantPlay)}</p>` : ""}
        <p class="endcard-eyebrow">${esc(L.nextLabel)}${counting ? ` · <span class="endcard-secs">${esc(L.inSecs(left))}</span>` : ""}</p>
        <a class="endcard-title" href="${href}" data-link>${esc(titleOf(next))}</a>
        <p class="endcard-meta"><span>${esc(DATA.channels[next.c].name)}</span><span class="endcard-dur">${fmtDur(next.d)}</span></p>
        <div class="endcard-actions">
          <a class="chip endcard-go" href="${href}" data-link${counting ? ` data-count style="--count:${COUNTDOWN}s"` : ""}>${esc(L.playNow)}</a>
          <button class="chip" type="button" data-endcard-cancel>${esc(L.cancel)}</button>
        </div>
      </div>
      <p class="sr-only" role="status">${esc(`${L.nextLabel}: ${titleOf(next)}`)}</p>
    </div>`;
    card.hidden = false;
    if (!counting) return;
    // One deadline drives the words. The fill on the button is a CSS animation of the same length.
    const secs = card.querySelector(".endcard-secs"), deadline = Date.now() + COUNTDOWN * 1000;
    clearInterval(this.tick);
    this.tick = setInterval(() => {
      if (!card.isConnected) return this.stopCountdown();
      left = Math.ceil((deadline - Date.now()) / 1000);
      if (left > 0) { secs.textContent = t().inSecs(left); return; }
      this.stopCountdown();
      goTo(href);
    }, 250);
  },
  onState(s) {
    if (s === this.lastState) return; // The embed reports each change through two channels.
    this.lastState = s;
    if (s === 0) this.showEndcard("ended");
    else if (s === 1 || s === 3) this.stopCountdown();
  },
};
window.addEventListener("message", (e) => {
  if (e.origin !== YT_ORIGIN || !player.frame || e.source !== player.frame.contentWindow) return;
  let msg;
  try { msg = typeof e.data === "string" ? JSON.parse(e.data) : e.data; } catch { return; }
  if (!msg || typeof msg !== "object") return;
  if (msg.event === "onReady" || msg.event === "initialDelivery") {
    if (!player.ready) {
      player.ready = true;
      player.command("addEventListener", ["onStateChange"]);
      player.command("addEventListener", ["onError"]);
    }
  } else if (msg.event === "onStateChange") player.onState(Number(msg.info));
  else if (msg.event === "infoDelivery" && msg.info && "playerState" in msg.info) player.onState(Number(msg.info.playerState));
  else if (msg.event === "onError") { player.lastState = "error"; player.showEndcard("error"); }
});
function goTo(href) {
  rememberPosition();
  history.pushState({}, "", href);
  route();
}

function viewChannels() {
  const L = t();
  document.title = `${L.navChannels} | MandarinTube`;
  main.innerHTML = `<h1 class="page-title">${esc(L.channelsTitle)}</h1>
    <p class="page-lead">${esc(L.channelsLead)} <a href="/?view=method" data-link>${esc(L.seeHow)}</a></p>
    <ol class="rank">${DATA.channels.map((c, i) => {
      const main_ = c.mainLevel ? L.mostly(levelName(levelOf(c.mainLevel)).toLowerCase()) : "";
      return `<li>
      <span class="pos">${i + 1}</span>
      <div><h2><a href="${channelHref(c)}" data-link>${esc(c.name)}</a></h2>
      <p>${esc(evidenceSentence(c))}</p>
      <p>${esc(L.countHere(fmtInt(c.count)))}${esc(main_)}.${c.cpm ? ` ${esc(L.speed(fmtInt(c.cpm)))}` : ""}</p></div>
    </li>`; }).join("")}</ol>`;
}

function viewChannel(key, restore) {
  const L = t(), idx = DATA.channels.findIndex((c) => c.key === key);
  if (idx < 0) {
    document.title = "MandarinTube";
    main.innerHTML = emptyBlock(L.channelMissing, "", `<a class="chip" href="/?view=channels" data-link>${esc(L.seeChannels)}</a>`);
    return;
  }
  const c = DATA.channels[idx];
  document.title = `${c.name} | MandarinTube`;
  const vids = VIDEOS.filter((v) => v.c === idx).sort((a, b) => b.s - a.s);
  const hid = state.hidden.includes(c.id);
  main.innerHTML = `<h1 class="page-title">${esc(c.name)}</h1>
    <p class="page-lead">${esc(evidenceSentence(c))}</p>
    ${(c.quotes || []).map((q) => `<blockquote class="quote" lang="en">${esc(q.text)}<a href="${esc(q.url)}" target="_blank" rel="noopener" lang="${state.lang}">${esc(L.redditYear(q.year))}</a></blockquote>`).join("")}
    <div class="actions">
      <a class="chip" href="https://www.youtube.com/channel/${esc(c.id)}" target="_blank" rel="noopener">${esc(L.openYt)}</a>
      <button class="chip" type="button" data-hide="${esc(c.id)}" aria-pressed="${hid}">${esc(hid ? L.hidden : L.hide)}</button>
    </div>
    <div class="grid" id="grid"></div>`;
  bindPager(vids, main.querySelector("#grid"), restore?.shown);
}

function viewSaved(tab, restore) {
  const L = t();
  document.title = `${L.savedTitle} | MandarinTube`;
  const tabs = [["liked", L.tabLiked], ["later", L.tabLater], ["history", L.tabHistory]];
  const active = tabs.some((x) => x[0] === tab) ? tab : "liked";
  const ids = active === "history" ? state.history.map((h) => h.id) : state[active];
  const list = ids.map((id) => BY_ID.get(id)).filter(Boolean);
  const empty = { liked: L.emptyLiked, later: L.emptyLater, history: L.emptyHistory }[active];
  main.innerHTML = `<h1 class="page-title">${esc(L.savedTitle)}</h1>
    <p class="page-lead">${esc(L.savedLead)}</p>
    <div class="tabs">
      ${tabs.map(([id, label]) => `<a class="chip" href="/?view=saved&tab=${id}" data-link ${id === active ? 'aria-current="page"' : ""}>${esc(label)}</a>`).join("")}
      ${active === "history" && list.length ? `<button class="chip" type="button" data-clear-history>${esc(L.clearHistory)}</button>` : ""}
    </div>
    ${list.length ? `<div class="grid" id="grid"></div>` : emptyBlock(empty[0], empty[1], `<a class="chip" href="/" data-link>${esc(L.browse)}</a>`)}`;
  if (list.length) bindPager(list, main.querySelector("#grid"), restore?.shown);
}

function viewMethod() {
  const L = t(), s = DATA.stats, m = DATA.method[state.lang];
  document.title = `${L.mTitle} | MandarinTube`;
  main.innerHTML = `<div class="prose">
    <h1 class="page-title">${esc(L.mTitle)}</h1>
    <p>${esc(L.mLead)}</p>
    <h2>${esc(L.mFrom)}</h2>
    <p>${esc(L.mFromBody(fmtInt(s.redditRows), s.redditFirst, DATA.method.seedNames))}</p>
    <h2>${esc(L.mRank)}</h2>
    <p>${esc(L.mRankLead)}</p>
    <ol>
      <li><strong>${esc(L.mRank1Title)}</strong> ${esc(L.mRank1)}</li>
      <li><strong>${esc(L.mRank2Title)}</strong> ${esc(m.fanText)}</li>
    </ol>
    <p>${esc(L.mGate)}</p>
    <h2>${esc(L.mListen)}</h2>
    <p>${esc(L.mListenBody)}</p>
    <h2>${esc(L.mAi)}</h2>
    <p>${esc(m.aiText)}</p>
    <ul>${m.aiChecks.map((x) => `<li>${esc(x.replace("{checked}", fmtInt(s.labelChecked)).replace("{total}", fmtInt(s.videos)))}</li>`).join("")}</ul>
    <p>${esc(m.aiLimit)}</p>
    <h2>${esc(L.mTitles)}</h2>
    <p>${esc(L.mTitlesBody)}</p>
    <h2>${esc(L.mLevels)}</h2>
    <p>${esc(m.levelText)}</p>
    <h2>${esc(L.mPrivacy)}</h2>
    <p>${esc(L.mPrivacyBody)}</p>
    <p>${esc(L.mThumbs(DATA.built))}</p>
    <h2>${esc(L.mBuild)}</h2>
    <p>${esc(L.mBuildBody)}</p>
    <pre class="prompt" lang="en" tabindex="0">${esc(DATA.method.buildPrompt)}</pre>
    <button class="chip" type="button" data-copy-prompt aria-live="polite">${esc(L.copy)}</button>
    <p class="credit"><a href="${QUANG}" target="_blank" rel="noopener">${esc(L.credit)}</a></p>
    <p><a href="${REPO}" target="_blank" rel="noopener">${esc(L.sourceCode)}</a></p>
  </div>`;
}

/* ---------- Routing: query strings need no server fallback ---------- */
function route(restore) {
  const q = new URLSearchParams(location.search);
  const view = q.get("view");
  const nav = q.get("v") ? "" : q.get("c") ? "channels" : view || "home";
  document.querySelectorAll("[data-nav]").forEach((a) => {
    if (a.dataset.nav === nav) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
  });
  main.querySelectorAll(".sentinel").forEach((s) => s.remove());
  shownNow = 0;
  player.stopCountdown();
  if (q.get("v")) viewWatch(q.get("v"));
  else if (q.get("c")) viewChannel(q.get("c"), restore);
  else if (view === "channels") viewChannels();
  else if (view === "saved") viewSaved(q.get("tab"), restore);
  else if (view === "method") viewMethod();
  else viewHome(restore);
  if (restore?.y !== undefined) window.scrollTo(0, restore.y);
}
const rememberPosition = () => history.replaceState({ y: window.scrollY, shown: shownNow }, "");

function applyLanguage() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll("[data-t]").forEach((el) => { el.textContent = t()[el.dataset.t]; });
  document.querySelectorAll("[data-lang]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === state.lang)));
}

document.addEventListener("click", (e) => {
  const link = e.target.closest("a[data-link]");
  if (link && !e.metaKey && !e.ctrlKey && !e.shiftKey && !e.altKey && e.button === 0) {
    e.preventDefault();
    rememberPosition();
    const url = new URL(link.href);
    // A deliberate trip home gets fresh recommendations. Back keeps the old order.
    if (!url.search) feedCache.clear();
    if (link.href !== location.href) history.pushState({}, "", link.href);
    route();
    window.scrollTo(0, 0);
    main.focus({ preventScroll: true });
    return;
  }
  const langBtn = e.target.closest("[data-lang]");
  if (langBtn) {
    if (langBtn.dataset.lang === state.lang) return;
    state.lang = langBtn.dataset.lang;
    store.write("lang", state.lang);
    applyLanguage();
    // Stay in the same place, so switching language never loses a video or the scroll position.
    if (DATA) {
      const iframe = main.querySelector("iframe");
      if (iframe) relabelWatch(); else route({ y: window.scrollY, shown: shownNow });
    }
    return;
  }
  const levelBtn = e.target.closest("[data-level]");
  if (levelBtn) {
    const id = Number(levelBtn.dataset.level);
    state.level = state.level === id ? null : id;
    store.write("level", state.level);
    main.querySelectorAll("[data-level]").forEach((b) => b.setAttribute("aria-pressed", String(Number(b.dataset.level) === state.level)));
    renderFeed();
    return;
  }
  const lenBtn = e.target.closest("[data-length]");
  if (lenBtn) {
    state.length = lenBtn.dataset.length;
    store.write("length", state.length);
    main.querySelectorAll("[data-length]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.length === state.length)));
    renderFeed();
    return;
  }
  if (e.target.closest("[data-reset]")) {
    state.level = null; state.length = "any"; state.query = "";
    store.write("level", null); store.write("length", "any");
    route();
    return;
  }
  const copyBtn = e.target.closest("[data-copy-prompt]");
  if (copyBtn) {
    const say = (text) => {
      copyBtn.textContent = text;
      setTimeout(() => { if (copyBtn.isConnected) copyBtn.textContent = t().copy; }, 2000);
    };
    navigator.clipboard.writeText(DATA.method.buildPrompt).then(() => say(t().copied), () => {
      // Clipboard access can be refused, so leave the text selected for a manual copy.
      getSelection().selectAllChildren(main.querySelector(".prompt"));
      say(t().copySelect);
    });
    return;
  }
  if (e.target.closest("[data-endcard-cancel]")) {
    player.stopCountdown();
    return;
  }
  const toggle = e.target.closest("[data-toggle]");
  if (toggle) {
    const { toggle: key, id } = toggle.dataset;
    const on = state[key].includes(id);
    state[key] = on ? state[key].filter((x) => x !== id) : [id, ...state[key]];
    store.write(key, state[key]);
    toggle.setAttribute("aria-pressed", String(!on));
    toggle.textContent = toggleLabel(key, !on);
    return;
  }
  const hide = e.target.closest("[data-hide]");
  if (hide) {
    const id = hide.dataset.hide, on = state.hidden.includes(id);
    state.hidden = on ? state.hidden.filter((x) => x !== id) : [...state.hidden, id];
    store.write("hidden", state.hidden);
    feedCache.clear();
    hide.setAttribute("aria-pressed", String(!on));
    hide.textContent = on ? t().hide : t().hidden;
    return;
  }
  const clear = e.target.closest("[data-clear-history]");
  if (clear) {
    if (clear.dataset.armed) {
      state.history = [];
      store.write("history", []);
      feedCache.clear();
      route();
    } else {
      // History can't be recovered, so it takes a second, deliberate press.
      clear.dataset.armed = "1";
      clear.textContent = t().clearConfirm;
      setTimeout(() => {
        if (!clear.isConnected) return;
        delete clear.dataset.armed;
        clear.textContent = t().clearHistory;
      }, 4000);
    }
  }
});

document.addEventListener("change", (e) => {
  if (!e.target.matches("[data-autoplay]")) return;
  state.autoplay = e.target.checked;
  store.write("autoplay", state.autoplay);
  // Turning it off mid-countdown stops it. Turning it on again waits for the next ending.
  if (!state.autoplay) player.stopCountdown();
});

// Reloading the page would restart the video, so the watch page swaps its words in place.
function relabelWatch() {
  const L = t(), q = new URLSearchParams(location.search), v = BY_ID.get(q.get("v"));
  if (!v) return;
  const c = DATA.channels[v.c], lvl = levelOf(v.l);
  document.title = `${titleOf(v)} | MandarinTube`;
  main.querySelector(".watch h1").textContent = titleOf(v);
  main.querySelector(".orig").hidden = titleOf(v) === v.t;
  main.querySelectorAll("[data-vid]").forEach((el) => { el.textContent = titleOf(BY_ID.get(el.dataset.vid)); });
  main.querySelectorAll("[data-toggle]").forEach((b) => { b.textContent = toggleLabel(b.dataset.toggle, b.getAttribute("aria-pressed") === "true"); });
  const yt = main.querySelector(".actions a.chip");
  if (yt) yt.textContent = L.openYt;
  const metaViews = main.querySelector(".watch .meta span");
  if (metaViews && v.v) metaViews.textContent = L.views(fmtCompact(v.v));
  const note = lvl ? (v.ls ? L.levelLabelled(levelName(lvl).toLowerCase()) : L.levelEstimated(levelName(lvl).toLowerCase())) : "";
  main.querySelector(".evidence h2").textContent = L.why;
  main.querySelector(".evidence p").textContent = `${evidenceSentence(c)} ${note}`;
  const aside = main.querySelector(".next");
  aside.setAttribute("aria-label", L.upNext);
  aside.querySelector("h2").textContent = L.upNext;
  aside.querySelector(".switch span").textContent = L.autoplay;
}

// "/" jumps to search, and Escape clears it. Neither fires while typing in the field.
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && player.tick) { player.stopCountdown(); return; }
  const search = main.querySelector(".search");
  if (!search) return;
  if (e.key === "/" && !e.metaKey && !e.ctrlKey && !e.altKey && document.activeElement !== search) {
    e.preventDefault();
    search.focus();
  } else if (e.key === "Escape" && document.activeElement === search && search.value) {
    search.value = "";
    state.query = "";
    renderFeed();
  }
});

history.scrollRestoration = "manual";
window.addEventListener("popstate", (e) => route(e.state || undefined));
window.addEventListener("pagehide", rememberPosition);

// A missing middle frame comes back as an error or a 120px grey placeholder.
function thumbFallback(img) {
  if (img.dataset.fellBack) return;
  img.dataset.fellBack = "1";
  img.src = `https://i.ytimg.com/vi/${img.dataset.id}/hqdefault.jpg`;
}
document.addEventListener("error", (e) => { if (e.target.tagName === "IMG" && e.target.dataset.id) thumbFallback(e.target); }, true);
document.addEventListener("load", (e) => {
  if (e.target.tagName === "IMG" && e.target.dataset.id && e.target.naturalWidth <= 120) thumbFallback(e.target);
}, true);

async function init() {
  applyLanguage();
  main.innerHTML = `<p class="status">${esc(t().loading)}</p>`;
  try {
    const res = await fetch("/data.json");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    DATA = await res.json();
  } catch (err) {
    main.innerHTML = emptyBlock(t().loadFailed(err.message), t().loadFix);
    return;
  }
  VIDEOS = DATA.videos.map(([id, c, title, d, v, ts, l, ls, s, vt]) => ({
    id, c, t: title, vt, d, v, ts, l, ls, s, q: fold(`${title} ${vt || ""} ${DATA.channels[c].name}`),
  }));
  BY_ID = new Map(VIDEOS.map((v) => [v.id, v]));
  route(history.state || undefined);
}
init();
