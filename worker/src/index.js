// Public quote proxy. Yahoo Finance is unofficial and may block requests or delay quotes.
const SYMBOLS={usdcny:"CNY=X",nasdaq:"^NDX",sp500:"^GSPC",gold:"GC=F",btc:"BTC-USD",sse:"000001.SS"};
const TTL=120;
async function quote(id){
 const code=encodeURIComponent(SYMBOLS[id]);
 let lastError="source unavailable";
 for(const host of ["query1.finance.yahoo.com","query2.finance.yahoo.com"]){
  try{
   const url="https://"+host+"/v8/finance/chart/"+code+"?range=5d&interval=1d";
   const res=await fetch(url,{headers:{"Accept":"application/json","User-Agent":"Mozilla/5.0"}});
   if(!res.ok)throw Error("HTTP "+res.status);
   const result=(await res.json()).chart?.result?.[0];
   const q=result?.indicators?.quote?.[0],stamps=result?.timestamp||[];
   const valid=stamps.map((ts,i)=>({ts,close:q?.close?.[i]})).filter(x=>Number.isFinite(x.close));
   if(valid.length<2)throw Error("insufficient observations");
   const latest=valid.at(-1),previous=valid.at(-2),delta=latest.close-previous.close;
   return {id,symbol:SYMBOLS[id],price:latest.close,previousClose:previous.close,change:delta,percent:delta/previous.close*100,marketTimestamp:latest.ts,source:"Yahoo Finance (unofficial, may be delayed)"};
  }catch(e){lastError=String(e)}
 }
 return {id,error:lastError};
}
async function getSnapshot(){
 const items=await Promise.all(Object.keys(SYMBOLS).map(quote));
 return {generatedAt:new Date().toISOString(),refreshSeconds:TTL,markets:Object.fromEntries(items.map(x=>[x.id,x]))};
}
export default {async fetch(request){
 const url=new URL(request.url);
 if(url.pathname!=="/api/quotes")return new Response("Not found",{status:404});
 if(request.method!=="GET")return new Response("Method not allowed",{status:405});
 const origin=request.headers.get("Origin");
 const headers={"Content-Type":"application/json; charset=utf-8","Cache-Control":"public, max-age=60, s-maxage=120","Access-Control-Allow-Origin":"https://finance.laoxu.org","Vary":"Origin","X-Content-Type-Options":"nosniff"};
 const cache=caches.default,cacheKey=new Request("https://finance-quotes-cache.invalid/snapshot");
 let response=await cache.match(cacheKey);
 if(!response){
  const body=JSON.stringify(await getSnapshot());
  response=new Response(body,{headers});
  if(Object.values(JSON.parse(body).markets).some(x=>!x.error))await cache.put(cacheKey,response.clone());
 }
 return new Response(response.body,{headers});
}};
