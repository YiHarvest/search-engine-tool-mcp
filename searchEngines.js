const https = require("https");

// 使用 Jina API 进行搜索（快速且可靠）
async function jinaSearch(query) {
  return new Promise((resolve, reject) => {
    const url = `https://api.jina.ai/search?q=${encodeURIComponent(query)}&limit=5`;
    
    https.get(url, { headers: { "User-Agent": "SearchAgent/1.0" } }, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try {
          const result = JSON.parse(data);
          const results = (result.data || []).map((item) => ({
            href: item.url,
            title: item.title,
            abstract: item.snippet || "",
          }));
          resolve(results);
        } catch {
          resolve([]);
        }
      });
    }).on("error", () => resolve([]));
  });
}

async function googleSearch(query) {
  return await jinaSearch(query);
}

async function bingSearch(query) {
  return await jinaSearch(query);
}

async function yahooSearch(query) {
  return await jinaSearch(query);
}

async function duckduckgoSearch(query) {
  return await jinaSearch(query);
}

module.exports = {
  googleSearch,
  bingSearch,
  yahooSearch,
  duckduckgoSearch,
};
