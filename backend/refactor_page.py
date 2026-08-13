import re

with open("../frontend/src/app/page.tsx", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add handleRemoveSavedProperty
remove_func = """  const handleRemoveSavedProperty = (id: string) => {
    setSavedProperties((prev) => {
      const updated = prev.filter((p) => p.id !== id);
      try {
        localStorage.setItem("rayic_saved_properties", JSON.stringify(updated));
      } catch (e) {}
      
      if (selectedPropertyId === id) {
        if (updated.length > 0) {
          setSelectedPropertyId(updated[0].id);
          setValuationData(updated[0].valuationData);
          setParsedInput(updated[0].inputData);
        } else {
          setSelectedPropertyId(null);
          setValuationData(null);
          setParsedInput(null);
          if (activeMenu !== "home" && activeMenu !== "add_property") {
            setActiveMenu("home");
          }
        }
      }
      return updated;
    });
  };"""

content = re.sub(
    r'(const handleSelectSavedProperty.*?};)',
    rf'\1\n\n{remove_func}',
    content,
    flags=re.DOTALL
)

# 2. Add onRemoveProperty to ProfilePortfolioView
content = re.sub(
    r'(<ProfilePortfolioView.*?onSelect=\{handleSelectSavedProperty\})',
    r'\1\n            onRemoveProperty={handleRemoveSavedProperty}',
    content,
    flags=re.DOTALL
)

# 3. Change AdInputParser from Modal to Menu View
# Remove ListingModal
content = re.sub(
    r'\{/\* Wizard Listing Modal \*/\}.*?</ListingModal>',
    r"""{/* MENU 7: ADD PROPERTY */}
        {activeMenu === "add_property" && (
          <AdInputParser
            onComplete={runFullCheckup}
            loading={loading}
          />
        )}""",
    content,
    flags=re.DOTALL
)

# 4. Change setIsParserOpen(true) to handleMenuChangeWithGuard("add_property") (wait, handleMenuChangeWithGuard might require an explicit argument, or I can just use setActiveMenu("add_property"))
content = re.sub(r'setIsParserOpen\(true\)', 'setActiveMenu("add_property" as any)', content)

# 5. In runFullCheckup:
content = re.sub(r'setIsParserOpen\(false\);', '', content)

with open("../frontend/src/app/page.tsx", "w", encoding="utf-8") as f:
    f.write(content)
print("page.tsx refactored.")
