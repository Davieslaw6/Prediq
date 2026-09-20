const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";
export async function getUpcoming(){const r=await fetch(`${API}/api/matches/upcoming`,{cache:"no-store"}); if(!r.ok)throw new Error("Failed to load matches"); return r.json()}
export async function getPrediction(id:number){const r=await fetch(`${API}/api/predictions/${id}`,{cache:"no-store"}); if(!r.ok)throw new Error(await r.text()); return r.json()}
