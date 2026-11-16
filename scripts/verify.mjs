// Read-only public receipt/source/state verifier. No signer and no write RPC methods.
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {createClient} from 'genlayer-js';
import {studionet} from 'genlayer-js/chains';
import {TransactionHashVariant} from 'genlayer-js/types';
import {validateStudioConsensus} from './studio-consensus.ts';
const root=new URL('../',import.meta.url),source=await readFile(new URL('contracts/evidence_registry.py',root),'utf8');
const sha=x=>createHash('sha256').update(x).digest('hex');
const deployment=JSON.parse(await readFile(new URL('evidence/deployment.json',root),'utf8'));
const client=createClient({chain:studionet,endpoint:'https://studio.genlayer.com/api'});
async function rpc(method,params=[]){const r=await fetch('https://studio.genlayer.com/api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:1,method,params}),signal:AbortSignal.timeout(60000)});if(!r.ok)throw Error('RPC HTTP '+r.status);const j=await r.json();if(j.error)throw Error(JSON.stringify(j.error));return j.result;}
if(await rpc('eth_chainId')!=='0xf22f')throw Error('Wrong chain');
if(sha(source)!==deployment.sourceSha256||sha(await client.getContractCode(deployment.address))!==sha(source))throw Error('Source mismatch');
for(const name of ['deploy','release-add','release-review','known-issues-add','known-issues-review','theme-add','theme-review','snapshot']){
 const proof=JSON.parse(await readFile(new URL('evidence/'+name+'.json',root),'utf8'));
 const tx=await rpc('eth_getTransactionByHash',[proof.hash]);
 if(tx.hash!==proof.hash||tx.from_address.toLowerCase()!==deployment.owner.toLowerCase()||tx.to_address.toLowerCase()!==deployment.address.toLowerCase())throw Error('Transaction identity mismatch');
 console.log(name,validateStudioConsensus(tx));
}
for(const {id,expected} of deployment.scenarios){
 const record=JSON.parse(await client.readContract({address:deployment.address,functionName:'get_decision',args:[id],transactionHashVariant:TransactionHashVariant.LATEST_FINAL}));
 const saved=JSON.parse(await readFile(new URL('evidence/'+id+'-decision.json',root),'utf8'));
 if(record.assessment.relation!==expected||JSON.stringify(record)!==JSON.stringify(saved))throw Error('Stored record mismatch');
 console.log(id,record.assessment.relation);
}
const snapshot=JSON.parse(await client.readContract({address:deployment.address,functionName:'get_snapshot',args:['complete'],transactionHashVariant:TransactionHashVariant.LATEST_FINAL}));
if(snapshot.status!=='CONFLICT')throw Error('Snapshot mismatch');
console.log('Public evidence verified; hosted simulator only.', snapshot.status);
