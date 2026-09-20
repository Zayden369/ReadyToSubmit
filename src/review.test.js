import {test} from 'node:test';import assert from 'node:assert/strict';import {reviewPacket,validateFile,samples,initialFields,docTypes} from './review.js';
test('sample flags mismatch and uncertain roll',()=>assert.deepEqual(reviewPacket(samples,initialFields,false).map(i=>i.id),['name','roll']));
test('explicit correction clears issues',()=>assert.equal(reviewPacket(samples,{...initialFields,bankName:initialFields.applicationName,roll:'126834'},true).length,0));
test('missing document remains visible',()=>assert.ok(reviewPacket({...samples,academic:null},initialFields,true).some(i=>i.id==='missing-academic')));
test('type size and empty upload errors',()=>{assert.ok(validateFile({name:'a.exe',size:1},docTypes[0]));assert.ok(validateFile({name:'a.pdf',size:6000000},docTypes[0]));assert.ok(validateFile({name:'a.pdf',size:0},docTypes[0]));assert.equal(validateFile({name:'a.pdf',size:100},docTypes[0]),'');});
