/* The transcripts of Lem's site: a ```text block whose every line starts with "you" or "lem" and
   two spaces, or with five spaces where a turn goes on, as on the home page. This script puts each
   turn in a span of its speaker's class, and the speaker's word in a span of its own, so that
   lem-site.css shows each speaker in its own hue. The text stays as it was, character for
   character, so the copy button copies the plain transcript. */
(() => {
  const turn = /^(you|lem) {2}/
  const goesOn = /^ {5}\S/

  function isTranscript (code) {
    const lines = code.textContent.replace(/\n$/, '').split('\n')
    return turn.test(lines[0]) && lines.every((line) => turn.test(line) || goesOn.test(line))
  }

  function speakerSpans (code) {
    const turns = code.textContent.split(/(?=^(?:you|lem) {2})/m)
    code.replaceChildren(...turns.map((text) => {
      const speaker = text.slice(0, 3)
      const word = document.createElement('span')
      word.className = 'lem-speaker'
      word.textContent = speaker
      const line = document.createElement('span')
      line.className = `lem-turn lem-turn-${speaker}`
      line.append(word, text.slice(speaker.length))
      return line
    }))
  }

  document.querySelectorAll('.language-text pre > code').forEach((code) => {
    if (isTranscript(code)) speakerSpans(code)
  })
})()
