/**
 * Hyperpersonalisation Lab: recibe las respuestas de la app de Streamlit
 * y las añade como filas en la pestaña "respuestas" de esta hoja de cálculo.
 */
const HEADERS = [
  'participant_id', 'timestamp_utc', 'position', 'id', 'is_fraud',
  'data_source', 'channel', 'rating', 'action', 'judged_fraud', 'rt_seconds'
];

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName('respuestas') || ss.insertSheet('respuestas');
    if (sheet.getLastRow() === 0) sheet.appendRow(HEADERS);

    const data = JSON.parse(e.postData.contents);
    const rows = (data.rows || []).map(r => HEADERS.map(h => r[h]));
    if (rows.length) {
      sheet.getRange(sheet.getLastRow() + 1, 1, rows.length, HEADERS.length).setValues(rows);
    }
    return ContentService.createTextOutput(JSON.stringify({ ok: true, saved: rows.length }))
      .setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}
