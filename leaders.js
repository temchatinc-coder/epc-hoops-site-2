function makeTable(headers, rows) {
  const table = document.createElement("table");
  table.style.borderCollapse = "collapse";
  table.style.marginBottom = "12px";
  table.style.fontSize = "0.9rem";

  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  headers.forEach((h) => {
    const th = document.createElement("th");
    th.textContent = h;
    th.style.borderBottom = "1px solid #ccc";
    th.style.padding = "4px 6px";
    th.style.textAlign = "left";
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    row.forEach((cell) => {
      const td = document.createElement("td");
      td.textContent = cell;
      td.style.padding = "3px 6px";
      td.style.borderBottom = "1px solid #eee";
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  return table;
}

fetch("epc_leaders.json")
  .then((r) => r.json())
  .then((data) => {
    // Update timestamp
    const updatedEl = document.getElementById("leaders-updated");
    if (updatedEl && data.generated_at) {
      updatedEl.textContent = data.generated_at;
    }

    // Player leaders
    const ppgDiv = document.getElementById("leaders-ppg");
    const ptsDiv = document.getElementById("leaders-pts");
    const threesDiv = document.getElementById("leaders-threes");
    const teamsDiv = document.getElementById("leaders-teams");

    const ppg = data.player_leaders?.points_per_game || [];
    const pts = data.player_leaders?.points_total || [];
    const threes = data.player_leaders?.three_pointers_made || [];
    const teamOff = data.team_leaders?.offense_points_per_game || [];

    if (ppgDiv) {
      ppgDiv.innerHTML = "";
      const rows = ppg.map((p, i) => [
        i + 1,
        p.player,
        p.team,
        `${p.ppg.toFixed(1)} ppg`,
        `${p.pts} pts`,
        `${p.gp} gp`,
      ]);
      ppgDiv.appendChild(
        makeTable(["#", "Player", "Team", "PPG", "Total Pts", "GP"], rows)
      );
    }

    if (ptsDiv) {
      ptsDiv.innerHTML = "";
      const rows = pts.map((p, i) => [
        i + 1,
        p.player,
        p.team,
        `${p.pts} pts`,
        `${p.gp} gp`,
      ]);
      ptsDiv.appendChild(
        makeTable(["#", "Player", "Team", "Total Pts", "GP"], rows)
      );
    }

    if (threesDiv) {
      threesDiv.innerHTML = "";
      const rows = threes.map((p, i) => [
        i + 1,
        p.player,
        p.team,
        p.threes,
        `${p.gp} gp`,
      ]);
      threesDiv.appendChild(
        makeTable(["#", "Player", "Team", "3PM", "GP"], rows)
      );
    }

    if (teamsDiv) {
      teamsDiv.innerHTML = "";
      const rows = teamOff.map((t, i) => [
        i + 1,
        t.team,
        `${t.ppg.toFixed(1)} ppg`,
        `${t.pts_for} pts`,
        `${t.gp} gp`,
      ]);
      teamsDiv.appendChild(
        makeTable(["#", "Team", "PPG", "Total Pts", "GP"], rows)
      );
    }
  })
  .catch((err) => {
    console.error("Error loading leaders:", err);
    const container = document.getElementById("leaders-container");
    if (container) {
      container.textContent = "Error loading leaders data.";
    }
  });
