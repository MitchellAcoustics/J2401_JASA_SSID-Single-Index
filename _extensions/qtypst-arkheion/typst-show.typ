// Typst custom formats typically consist of a 'typst-template.typ' (which is
// the source code for a typst template) and a 'typst-show.typ' which calls the
// template's function (forwarding Pandoc metadata values as required)
//
// This is an example 'typst-show.typ' file (based on the default template  
// that ships with Quarto). It calls the typst function named 'article' which 
// is defined in the 'typst-template.typ' file. 
//
// If you are creating or packaging a custom typst template you will likely
// want to replace this file and 'typst-template.typ' entirely. You can find
// documentation on creating typst templates here and some examples here:
//   - https://typst.app/docs/tutorial/making-a-template/
//   - https://github.com/typst/templates

#show: doc => arkheion(
  $if(title)$
    title: "$title$",
  $endif$
  $if(by-author)$
    authors: (
  $for(by-author)$
  $if(it.name.literal)$
      ( name: "$it.name.literal$",
        affiliation: [$for(it.affiliations)$$it.name$$sep$, $endfor$],
        email: [$it.email$],
        orcid: "$it.orcid$" ),
  $endif$
  $endfor$
    ),
  $endif$
  $if(abstract)$
    abstract: [$abstract$],
  $endif$
  $if(date)$
    date: "$date$",
  $endif$
  $if(keywords)$
    keywords: ($for(keywords)$"$it$"$sep$, $endfor$),
  $endif$
  $if(bib-file)$
    bib: "$bib-file$",
  $endif$
  $if(cite-style)$
    cite: "$cite-style$",
  $endif$

  doc
)
