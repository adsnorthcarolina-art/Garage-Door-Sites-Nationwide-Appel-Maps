// Cloudflare Pages (advanced mode): serve one site per hostname from sites/<domain>/
const DEFAULT = "charlottegaragedoorrepair.net";
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    let host = url.hostname.toLowerCase();
    const isPagesDev = host.endsWith(".pages.dev");
    // apex -> www (301), keeps path and query
    if (!isPagesDev && !host.startsWith("www.")) {
      url.hostname = "www." + host;
      return Response.redirect(url.toString(), 301);
    }
    host = host.replace(/^www\./, "");
    const site = isPagesDev ? DEFAULT : host;
    const assetUrl = new URL(request.url);
    // photos are shared by every site: /img/* -> /_shared/img/*
    const im = url.pathname.match(/^\/img\/[^/]+\/([^/]+\.webp)$/);
    assetUrl.pathname = im ? "/_shared/img/" + im[1] : "/" + site + url.pathname;
    const res = await env.ASSETS.fetch(new Request(assetUrl.toString(), request));
    if (res.status === 404) {
      const nf = await env.ASSETS.fetch(new Request(new URL("/" + site + "/404.html", request.url).toString(), request));
      if (nf.ok) return new Response(nf.body, { status: 404, headers: nf.headers });
    }
    return res;
  },
};
