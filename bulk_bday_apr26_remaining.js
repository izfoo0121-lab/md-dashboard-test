// Paste into browser console on admin.html or campaign_audit.html
// Marks remaining April Birthday Gift debtors as delivered
// Per spreadsheet: CJ=1, JACKY=1, JAMES=6, KEE=10, KF=4, KI-MI=2, KW=2, LEON=6, NMK=1, YI=3 = 36 total
// Note: KEAN already 100%, BEN = 0 target — both excluded

(async function() {

  // Per-agent debtor codes (from dashboard_data.json, trimmed to spreadsheet counts)
  const PER_AGENT = {
    'CJ':    ['300-J055'],
    'JACKY': ['300-KT186'],
    'JAMES': ['300-JS009','300-JS044','300-JS084','300-JS114','300-JS142','300-JS238'],
    'KEE':   ['300-H052','300-H138','300-J096','300-J125','300-WK024','300-WK032',
               '300-WK036','300-J154','300-WK056','300-WK079'],
    'KF':    ['300-BY045','300-BY046','300-BY219','300-BY040'],
    'KI-MI': ['300-KM048','300-KM065'],
    'KW':    ['300-C117','300-C417'],
    'LEON':  ['300-D086','300-D091','300-D107','300-D191','300-D195','300-D241'],
    'NMK':   ['300-KH076'],
    'YI':    ['300-KV005','300-KV026','300-KV046'],
  };

  const MONTH    = 'Apr26';
  const CAMP_ID  = 'birthday_gift_auto';
  const ts       = '20 Apr';
  const claimData = { status:'delivered', ts, bulk:true, remark:'April birthday gift confirmed' };

  let written = 0, skipped = 0;

  Object.entries(PER_AGENT).forEach(([agent, codes]) => {
    codes.forEach(code => {
      const key = `camp_claim_${MONTH}_${agent}_${CAMP_ID}_${code}`;
      if (!localStorage.getItem(key)) {
        localStorage.setItem(key, JSON.stringify(claimData));
        written++;
      } else {
        skipped++;
      }
    });
  });

  console.log(`✓ Written ${written} new records, ${skipped} already existed`);

  // Push to Gist
  if (typeof GistSync !== 'undefined' && GistSync.isConfigured()) {
    const fileKey = `claims_${MONTH}`;
    const cache   = JSON.parse(localStorage.getItem('md_gist_cache') || '{}');
    if (!cache[fileKey]) cache[fileKey] = {};

    Object.entries(PER_AGENT).forEach(([agent, codes]) => {
      codes.forEach(code => {
        cache[fileKey][`${agent}_${CAMP_ID}_${code}`] = claimData;
      });
    });

    localStorage.setItem('md_gist_cache', JSON.stringify(cache));
    const ok = await GistSync.push(fileKey, cache[fileKey]);
    console.log(ok ? '✓ Pushed to Gist' : '⚠ Gist push failed — saved locally only');
  } else {
    console.log('⚠ GistSync not available — saved to localStorage only. Open admin.html and push manually.');
  }

  // Count total marked
  const total = Object.values(PER_AGENT).reduce((s, arr) => s + arr.length, 0);
  alert(`✓ Done!\n${written} new records written, ${skipped} already existed.\nTotal: ${total} debtors marked as April Birthday Gift delivered.\n\nRefresh the page to see updated counts.`);

})();
