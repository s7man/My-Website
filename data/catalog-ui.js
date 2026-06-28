const catalog = window.notesCatalog || [];
const semesterNav = document.querySelector("#semesterNav");
const catalogRoot = document.querySelector("#catalogRoot");
const searchForm = document.querySelector("#searchForm");
const searchInput = document.querySelector("#noteSearch");
const emptyState = document.querySelector("#emptyState");

// Checks whether a text block contains the current search query.
function textMatches(text, query) {
  return text.toLowerCase().includes(query);
}

// Counts only available unit links inside one semester.
function getUnitCount(semester) {
  return semester.subjects.reduce((total, subject) => {
    return total + subject.units.filter((unit) => unit.available).length;
  }, 0);
}

// Builds one searchable text string from semester, subject, and unit data.
function getSearchText(semester, subject, unit) {
  return [
    semester.title,
    semester.description,
    subject?.name,
    subject?.fullName,
    subject?.description,
    unit?.title,
    unit?.summary,
    unit?.keywords
  ].filter(Boolean).join(" ");
}

// Creates the row of semester shortcut buttons from the catalog data.
function createSemesterNav() {
  semesterNav.innerHTML = "";

  catalog.forEach((semester) => {
    const link = document.createElement("a");
    link.className = "semester-link";
    link.href = `#${semester.id}`;
    link.innerHTML = `
      <span>${semester.title}</span>
      <small>${semester.subjects.length} subjects</small>
    `;
    semesterNav.append(link);
  });
}

// Creates one unit card, using a link when notes are available.
function createUnitCard(unit) {
  const element = document.createElement(unit.available ? "a" : "article");
  element.className = `unit-card${unit.available ? "" : " unavailable"}`;

  if (unit.available) {
    element.href = unit.href;
  } else {
    element.setAttribute("aria-disabled", "true");
  }

  element.innerHTML = `
    <span class="card-tag">${unit.available ? "Available" : "Coming soon"}</span>
    <h4>${unit.title}</h4>
    <p>${unit.summary}</p>
    <span class="card-link">${unit.available ? "Open notes" : "Not available yet"}</span>
  `;

  return element;
}

// Adds the placeholder message for semesters that have no subjects yet.
function addEmptySemesterMessage(subjectList) {
  const emptyMessage = document.createElement("p");
  emptyMessage.className = "empty-inline";
  emptyMessage.textContent = "Subjects will appear here when notes are added.";
  subjectList.append(emptyMessage);
}

// Creates one subject block and fills it with visible unit cards.
function createSubjectBlock(subject, visibleUnits) {
  const subjectBlock = document.createElement("article");
  subjectBlock.className = "subject-block";
  subjectBlock.innerHTML = `
    <div class="subject-header">
      <div>
        <p class="eyebrow">Subject</p>
        <h4>${subject.name}</h4>
        <p><strong>${subject.fullName}</strong> ${subject.description}</p>
      </div>
      <span class="count-pill">${subject.units.length} units</span>
    </div>
  `;

  const unitGrid = document.createElement("div");
  unitGrid.className = "unit-grid";
  visibleUnits.forEach((unit) => unitGrid.append(createUnitCard(unit)));
  subjectBlock.append(unitGrid);

  return subjectBlock;
}

// Renders all semesters, subjects, and units that match the current search.
function renderCatalog() {
  const query = searchInput.value.trim().toLowerCase();
  catalogRoot.innerHTML = "";
  let visibleSemesterCount = 0;

  catalog.forEach((semester) => {
    const semesterText = getSearchText(semester);
    const semesterMatches = !query || textMatches(semesterText, query);
    const semesterSection = document.createElement("section");
    const subjectList = document.createElement("div");
    const subjectCount = semester.subjects.length;
    const unitCount = getUnitCount(semester);
    let visibleSubjectCount = 0;

    semesterSection.className = "semester-panel";
    semesterSection.id = semester.id;
    subjectList.className = "subject-list";
    semesterSection.innerHTML = `
      <div class="semester-header">
        <div>
          <p class="eyebrow">Semester</p>
          <h3>${semester.title}</h3>
          <p>${semester.description}</p>
        </div>
        <span class="count-pill">${subjectCount} subjects / ${unitCount} units</span>
      </div>
    `;

    semester.subjects.forEach((subject) => {
      const subjectText = getSearchText(semester, subject);
      const subjectMatches = semesterMatches || textMatches(subjectText, query);
      const visibleUnits = subject.units.filter((unit) => {
        return subjectMatches || textMatches(getSearchText(semester, subject, unit), query);
      });

      if (!subjectMatches && visibleUnits.length === 0) return;

      subjectList.append(createSubjectBlock(subject, visibleUnits));
      visibleSubjectCount += 1;
    });

    if (subjectCount === 0 && semesterMatches) {
      addEmptySemesterMessage(subjectList);
    }

    if (visibleSubjectCount > 0 || (subjectCount === 0 && semesterMatches)) {
      semesterSection.append(subjectList);
      catalogRoot.append(semesterSection);
      visibleSemesterCount += 1;
    }
  });

  emptyState.hidden = visibleSemesterCount !== 0;
}

// Moves the page to the first visible result after pressing Search.
function scrollToSearchResult() {
  const target = catalogRoot.querySelector(".semester-panel") || emptyState;
  target.scrollIntoView({ behavior: "smooth", block: "start" });
}

// Handles the Search button without refreshing the page.
function handleSearchSubmit(event) {
  event.preventDefault();
  renderCatalog();
  scrollToSearchResult();
}

// Starts catalog rendering and search behavior on the homepage.
function initCatalog() {
  if (!semesterNav || !catalogRoot || !searchForm || !searchInput || !emptyState) return;

  createSemesterNav();
  renderCatalog();
  searchForm.addEventListener("submit", handleSearchSubmit);
  searchInput.addEventListener("input", renderCatalog);
}

initCatalog();
