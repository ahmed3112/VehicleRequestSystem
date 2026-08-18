export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const cors = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    };
    if (request.method === 'OPTIONS') return new Response(null, {headers:cors});
    try {
      if (url.pathname === '/api/health') return json({ok:true, database:'D1 SQLite'});
      if (url.pathname === '/api/data' && request.method === 'GET') {
        const lines = await env.DB.prepare('SELECT * FROM lines ORDER BY name').all();
        const vehicles = await env.DB.prepare('SELECT * FROM vehicles ORDER BY plate_number').all();
        return json({lines: lines.results, vehicles: vehicles.results}, cors);
      }
      if (url.pathname === '/api/lines' && request.method === 'POST') {
        const b = await request.json();
        const id = b.id || crypto.randomUUID();
        await env.DB.prepare('INSERT INTO lines(id,name) VALUES(?,?)').bind(id, String(b.name||'').trim()).run();
        return json({id,name:b.name}, cors, 201);
      }
      if (url.pathname.startsWith('/api/lines/') && request.method === 'PUT') {
        const id = url.pathname.split('/').pop(); const b=await request.json();
        await env.DB.prepare('UPDATE lines SET name=? WHERE id=?').bind(String(b.name||'').trim(),id).run();
        return json({ok:true},cors);
      }
      if (url.pathname.startsWith('/api/lines/') && request.method === 'DELETE') {
        const id=url.pathname.split('/').pop();
        const c=await env.DB.prepare('SELECT COUNT(*) c FROM vehicles WHERE line_id=?').bind(id).first();
        if (Number(c?.c||0)>0) return json({error:'LINE_HAS_VEHICLES'},cors,409);
        await env.DB.prepare('DELETE FROM lines WHERE id=?').bind(id).run(); return json({ok:true},cors);
      }
      if (url.pathname === '/api/vehicles' && request.method === 'POST') {
        const b=await request.json(); const id=b.id||crypto.randomUUID();
        await env.DB.prepare(`INSERT INTO vehicles(id,parking_name,plate_number,owner_name,chassis,line_id,phone,card_no,passengers,license_image) VALUES(?,?,?,?,?,?,?,?,?,?)`).bind(id,b.parking_name||'',b.plate_number||'',b.owner_name||'',b.chassis||'',b.line_id||null,b.phone||'',b.card_no||'',b.passengers||'',b.license_image||'').run();
        return json({id},cors,201);
      }
      if (url.pathname.startsWith('/api/vehicles/') && request.method === 'PUT') {
        const id=url.pathname.split('/').pop(); const b=await request.json();
        await env.DB.prepare(`UPDATE vehicles SET parking_name=?,plate_number=?,owner_name=?,chassis=?,line_id=?,phone=?,card_no=?,passengers=?,license_image=?,updated_at=CURRENT_TIMESTAMP WHERE id=?`).bind(b.parking_name||'',b.plate_number||'',b.owner_name||'',b.chassis||'',b.line_id||null,b.phone||'',b.card_no||'',b.passengers||'',b.license_image||'',id).run();
        return json({ok:true},cors);
      }
      if (url.pathname.startsWith('/api/vehicles/') && request.method === 'DELETE') {
        const id=url.pathname.split('/').pop(); await env.DB.prepare('DELETE FROM vehicles WHERE id=?').bind(id).run(); return json({ok:true},cors);
      }
      return json({error:'Not Found'},cors,404);
    } catch(e) { return json({error:e.message},cors,500); }
  }
};
function json(data, headers={}, status=200){return new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json',...headers}})}
