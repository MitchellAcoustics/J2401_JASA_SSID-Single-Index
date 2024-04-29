// Some definitions presupposed by pandoc's typst output.
#let blockquote(body) = [
  #set text( size: 0.92em )
  #block(inset: (left: 1.5em, top: 0.2em, bottom: 0.2em))[#body]
]

#let horizontalrule = [
  #line(start: (25%,0%), end: (75%,0%))
]

#let endnote(num, contents) = [
  #stack(dir: ltr, spacing: 3pt, super[#num], contents)
]

#show terms: it => {
  it.children
    .map(child => [
      #strong[#child.term]
      #block(inset: (left: 1.5em, top: -0.4em))[#child.description]
      ])
    .join()
}

// Some quarto-specific definitions.

#show raw.where(block: true): block.with(
    fill: luma(230), 
    width: 100%, 
    inset: 8pt, 
    radius: 2pt
  )

#let block_with_new_content(old_block, new_content) = {
  let d = (:)
  let fields = old_block.fields()
  fields.remove("body")
  if fields.at("below", default: none) != none {
    // TODO: this is a hack because below is a "synthesized element"
    // according to the experts in the typst discord...
    fields.below = fields.below.amount
  }
  return block.with(..fields)(new_content)
}

#let empty(v) = {
  if type(v) == "string" {
    // two dollar signs here because we're technically inside
    // a Pandoc template :grimace:
    v.matches(regex("^\\s*$")).at(0, default: none) != none
  } else if type(v) == "content" {
    if v.at("text", default: none) != none {
      return empty(v.text)
    }
    for child in v.at("children", default: ()) {
      if not empty(child) {
        return false
      }
    }
    return true
  }

}

#show figure: it => {
  if type(it.kind) != "string" {
    return it
  }
  let kind_match = it.kind.matches(regex("^quarto-callout-(.*)")).at(0, default: none)
  if kind_match == none {
    return it
  }
  let kind = kind_match.captures.at(0, default: "other")
  kind = upper(kind.first()) + kind.slice(1)
  // now we pull apart the callout and reassemble it with the crossref name and counter

  // when we cleanup pandoc's emitted code to avoid spaces this will have to change
  let old_callout = it.body.children.at(1).body.children.at(1)
  let old_title_block = old_callout.body.children.at(0)
  let old_title = old_title_block.body.body.children.at(2)

  // TODO use custom separator if available
  let new_title = if empty(old_title) {
    [#kind #it.counter.display()]
  } else {
    [#kind #it.counter.display(): #old_title]
  }

  let new_title_block = block_with_new_content(
    old_title_block, 
    block_with_new_content(
      old_title_block.body, 
      old_title_block.body.body.children.at(0) +
      old_title_block.body.body.children.at(1) +
      new_title))

  block_with_new_content(old_callout,
    new_title_block +
    old_callout.body.children.at(1))
}

#show ref: it => locate(loc => {
  let target = query(it.target, loc).first()
  if it.at("supplement", default: none) == none {
    it
    return
  }

  let sup = it.supplement.text.matches(regex("^45127368-afa1-446a-820f-fc64c546b2c5%(.*)")).at(0, default: none)
  if sup != none {
    let parent_id = sup.captures.first()
    let parent_figure = query(label(parent_id), loc).first()
    let parent_location = parent_figure.location()

    let counters = numbering(
      parent_figure.at("numbering"), 
      ..parent_figure.at("counter").at(parent_location))
      
    let subcounter = numbering(
      target.at("numbering"),
      ..target.at("counter").at(target.location()))
    
    // NOTE there's a nonbreaking space in the block below
    link(target.location(), [#parent_figure.at("supplement") #counters#subcounter])
  } else {
    it
  }
})

// 2023-10-09: #fa-icon("fa-info") is not working, so we'll eval "#fa-info()" instead
#let callout(body: [], title: "Callout", background_color: rgb("#dddddd"), icon: none, icon_color: black) = {
  block(
    breakable: false, 
    fill: background_color, 
    stroke: (paint: icon_color, thickness: 0.5pt, cap: "round"), 
    width: 100%, 
    radius: 2pt,
    block(
      inset: 1pt,
      width: 100%, 
      below: 0pt, 
      block(
        fill: background_color, 
        width: 100%, 
        inset: 8pt)[#text(icon_color, weight: 900)[#icon] #title]) +
      block(
        inset: 1pt, 
        width: 100%, 
        block(fill: white, width: 100%, inset: 8pt, body)))
}

#let arkheion(
  title: "",
  abstract: [],
  keywords: (),
  authors: (),
  date: none,
  bib: none,
  appendics: false,
  body,
) = {
  // Set the document's basic properties.
  set document(author: authors.map(a => a.name), title: title)
  set page(
    margin: (left: 25mm, right: 25mm, top: 25mm, bottom: 30mm),
    numbering: "1",
    number-align: center,
  )
  set text(font: "New Computer Modern", lang: "en")
  show math.equation: set text(weight: 400)
  show math.equation: set block(spacing: 0.65em)
  set math.equation(numbering: "(1)")
  set heading(numbering: "1.1")

  set cite(style: "chicago-author-date")


  // Set run-in subheadings, starting at level 4.
  show heading: it => {
    // H1 and H2
    if it.level == 1 {
      pad(
        bottom: 10pt,
        it
      )
    }
    else if it.level == 2 {
      pad(
        bottom: 8pt,
        it
      )
    }
    else if it.level > 3 {
      text(11pt, weight: "bold", it.body + " ")
    } else {
      it
    }
  }

  // Set the table style
  show table: set table(
    align: center,
    row-gutter: (2pt, auto),
    stroke: 0.5pt,
    inset: 5pt,
  )
  

  line(length: 100%, stroke: 2pt)
  // Title row.
  pad(
    bottom: 4pt,
    top: 4pt,
    align(center)[
      #block(text(weight: 500, 1.75em, title))
      #v(1em, weak: true)
    ]
  )
  line(length: 100%, stroke: 2pt)

  // Author information.
  pad(
    top: 0.5em,
    x: 2em,
    grid(
      columns: (1fr,) * calc.min(3, authors.len()),
      gutter: 1em,
      ..authors.map(author => align(center)[
        #if author.keys().contains("orcid") {
          link("http://orcid.org/" + author.orcid)[
            #pad(bottom: -8pt,
              grid(
                columns: (8pt, auto, 8pt),
                rows: 10pt,
                [],
                [*#author.name*],
                [
                  #pad(left: 4pt, top: -4pt, image("_extensions/qtypst-arkheion/res/orcid.svg", width: 8pt))
                ]
              )
            )
          ]
        } else {
          grid(
            columns: (auto),
            rows: 2pt,
            [*#author.name*],
          )
        }
        #author.email \
        #author.affiliation
      ]),
    ),
  )

  align(center)[#date]

  // Abstract.
  pad(
    x: 3em,
    top: 1em,
    bottom: 0.4em,
    align(center)[
      #heading(
        outlined: false,
        numbering: none,
        text(0.85em, smallcaps[Abstract]),
      )
      #set par(justify: true)
      #set text(hyphenate: false)

      #abstract
    ],
  )

  // Keywords
  if keywords.len() > 0 {
      [*_Keywords_* #h(0.3cm)] + keywords.map(str).join(" · ")
  }
  // Main body.
  set par(justify: true)
  set text(hyphenate: false)

  body

  // Add bibliography and create Bibiliography section
  // bibliography(bib)

}

#let arkheion-appendices(body) = {
  counter(heading).update(0)
  counter("appendices").update(1)

  set heading(
    numbering: (..nums) => {
      let vals = nums.pos()
      let value = "ABCDEFGHIJ".at(vals.at(0) - 1)
      if vals.len() == 1 {
        return "APPENDIX " + value
      }
      else {
        return value + "." + nums.pos().slice(1).map(str).join(".")
      }
    }
  );
  [#pagebreak() #body]
}
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
      title: "SPI - Defining bespoke and archetypal context-dependent Soundscape Perception Indices",
        authors: (
          ( name: "Andrew Mitchell",
        affiliation: [University College London],
        email: [andrew.mitchell.18\@ucl.ac.uk],
        orcid: "" ),
            ( name: "Francesco Aletta",
        affiliation: [University College London],
        email: [f.aletta\@ucl.ac.uk],
        orcid: "" ),
            ( name: "Tin Oberman",
        affiliation: [University College London],
        email: [t.oberman\@ucl.ac.uk],
        orcid: "" ),
            ( name: "Jian Kang",
        affiliation: [],
        email: [j.kang\@ucl.ac.uk],
        orcid: "" ),
        ),
        abstract: [The soundscape approach provides a basis for considering the holistic perception of sound environments, in context. While steady advancements have been made in methods for assessment and analysis, a gap exists for comparing soundscapes and quantifying improvements in the multi-dimensional perception of a soundscape. To this end, there is a need for the creation of single value indices to compare soundscape quality which incorporate context, aural diversity, and specific design goals for a given application. Just as a variety of decibel-based indices have been developed for various purposes \(e.g.~$L_(A e q)$, $L_(C e q)$, $L_90$, $L d e n$, etc.), the soundscape approach requires the ability to create novel indices for different uses, but which share a common language and understanding. We therefore propose a unified framework for creating both bespoke and standardised single index measures of soundscape perception based on the soundscape circumplex model, allowing for new metrics to be defined in the future. The implementation of this framework is demonstrated through the creation of a public spaced typology-based index using data collected under the SSID Protocol, which was designed specifically for the purpose of defining soundscape indices. Indices developed under this framework can enable a broader and more efficient application of the soundscape approach.

],
        date: "2024-04-29",
        keywords: ("keyword1", "keyword2"),
        bib: "FellowshipRefs-biblatex.bib",
    
  doc
)


= Introduction
<introduction>
The EU Green Paper on Future Noise Policy indicates that 80 million EU citizens are suffering from unacceptable environmental noise levels, according to the WHO recommendation #cite(<Berglund1999Guidelines>) and the social cost of transport noise is 0.2-2% of total GDP. The publication of the EU Directive Relating to the Assessment and Management of Environmental Noise \(END) #cite(<EuropeanUnion2002Directive>) in 2002 has led to major actions across Europe, with reducing noise levels as the focus, for which billions of Euros are being spent. However, it is widely recognised that solely reducing sound level is not always feasible or cost-effective, and more importantly, with only \~30% of environmental noise annoyance depending on facets of parameters such as acoustic energy #cite(<Guski1997Psychological>);, sound level reduction will not necessarily lead to improved quality of life.

Soundscape design, separate from noise control engineering, is about the relationships between human physiology, perception, the sound environment, and its social/cultural context #cite(<Kang2006Urban>);. Soundscape research represents a paradigm shift in that it combines physical, social, and psychological approaches and considers environmental sounds as a 'resource' rather than 'waste' #cite(<Kang2016Soundscape>) relating to perceptual constructs rather than just physical phenomena. However, the current research is still at the stage of describing and identifying the problems and tends to be fragmented and focussed on only special cases e.g.~subjective evaluations of soundscapes for residential areas #cite(<SchulteFortkamp2013Introduction>);. In the movement from noise control to soundscape creation #cite(<Aletta2015Soundscape>);, a vital step is the standardisation of methods to assess soundscape quality.

A common aim for implementing soundscape assessment in practice is to compare the quality of different soundscapes. Often \(but not always) the goal is to identify a 'good' soundscape compared to a 'bad' soundscape. However, this presents several challenges:

- What makes a soundscape good or bad is highly contextual;
- On what metric should the quality rating be based?
- How can we deal with different requirements and definitions of how a soundscape should be perceived?

In many cases, the ultimate aim is to be able to rank soundscapes based on their quality. However, any ranking metric should be flexible and be able to handle a variety of contexts and definitions of what a 'good' soundscape is for a given purpose. To address this, we will propose the Soundscape Perception Index \(SPI) framework, a flexible method for defining single value indices of soundscape quality based on distributions within the Soundscape Circumplex Model \(SCM) #cite(<Axelsson2010principal>)[, #cite(<Axelsson2012Swedish>);, #cite(<Mitchell2022How>);];.

The primary motivation behind the development of the Soundscape Perception Indices \(SPIs) framework stems from the need to address the existing gap in quantifying and comparing soundscape quality across diverse contexts and applications. By creating a unified framework for defining these indices, the aim is to facilitate a broader and more efficient application of the soundscape approach in various domains, such as urban planning, environmental management, acoustic design, and policy development.

The overarching aim of this framework is to empower stakeholders, decision-makers, and researchers with the ability to create tailored indices that align with their specific objectives and design goals, while simultaneously enabling cross-comparisons and benchmarking against empirically-defined soundscape archetypes. This dual approach not only acknowledges the context-dependent nature of soundscape perception but also fosters a common language and understanding, facilitating knowledge sharing and collaborative efforts within the field. This paper will demonstrate the SPI framework and test whether it is capable of both scoring soundscape quality and generating consistent rankings of soundscapes across different contexts.

= Background
<background>
In #cite(<Aletta2016Soundscape>);, the authors defined a framework for categorising the components of a soundscape assessment. They define three aspects: soundscape descriptors, soundscape indicators, and soundscape indices. Soundscape descriptors are defined as 'measures of how people perceive the acoustic environment' and soundscape indicators as 'measures used to predict the value of a soundscape descriptor'. Indices, the primary focus of this article, are single numerical values that combine multiple indicators or descriptors to provide a comprehensive representation of the overall soundscape perception and allow for comparison between soundscapes. These indices serve as powerful tools for quantifying and comparing soundscapes, enabling decision-makers and stakeholders to assess the impact of interventions, monitor changes over time, and prioritize areas for improvement#cite(<Kang2019Towards>);.

The earliest and most commonly used scientific index measuring sound level is the Decibel \(dB). To represent the overall level of sound with a single value on one scale, as the Decibel index does, is often desirable. For this purpose, a number of different values representing sounds at various frequencies must be combined. Several frequency weighting networks have been developed since the 1930s, considering typical human responses to sound based on equal-loudness-level contours #cite(<Fletcher1933Loudness>) and, among them, the A-weighting network, with resultant decibel values called dBA, has been commonly used in almost all the national/international regulations #cite(<Kryter1970Effects>);. However, there have been numerous criticisms on its effectiveness #cite(<Parmanen2007weighted>) as the correlations between dBA and perceived sound quality \(e.g.~noise annoyance) are often low #cite(<Hellman1987Why>);.

Another set of indices is psychoacoustic magnitudes, including loudness, fluctuation strength or roughness, sharpness, and pitch strength, development with sound quality studies of industrial products since the 1980’s #cite(<Zwicker2007Psychoacoustics>);. These emerged when it was conceived that acoustic emissions can be characterised beyond just sound level #cite(<Blauert1997Sound>);. But while psychoacoustic magnitudes have proven to be successful for the assessment of product sound quality, in the field of environmental acoustics, their applicability has been limited #cite(<Fastl2006Psychoacoustic>);, since a significant feature of environmental acoustics is that there are multiple/dynamic sound sources. Additionally, while pyschoacoustic magnitudes incorporate perceptual aspects, both dB based and pyschoacoustic indicies are ultimately describing the acoustic signal and not the soundscape perception and may therefore be more accurately described as indicators rather than soundscape indices #cite(<Mitchell2023conceptual>);.

When applied to urban sound and specifically to noise pollution, the soundscape approach introduces three key considerations beyond traditional noise control methods:

+ considering all aspects of the environment which may influence perception, not just the sound level and spectral content;
+ an increased and integrated consideration of the varying impacts which different sound sources and sonic characteristics have on perception; and
+ a consideration of both the positive and negative dimensions of soundscape perception.

This approach can enable better outcomes by identifying positive soundscapes \(in line with the END’s mandate to \`preserve environmental noise quality where it is good’ #cite(<EuropeanUnion2002Directive>);), better identify specific sources of noise which impact soundscape quality and pinpoint the characteristics which may need to be decreased, and illuminate alternative methods which could be introduced to improve a soundscape where a reduction of noise is impractical #cite(<Fiebig2018Does>);#cite(<Kang2018Impact>);. These can all lead to more opportunities to truly improve a space by identifying the causes of positive soundscapes, while also potentially decreasing the costs of noise mitigation by offering more targeted techniques and alternative approaches.

The traditional focus on noise levels alone fails to capture the complexity of soundscape perception, which encompasses a multitude of factors beyond mere sound pressure levels. Factors such as the presence of natural or human-made sounds, their temporal patterns, and the overall contextual meaning ascribed to these sounds all contribute to the holistic perception of a soundscape. Consequently, there is a pressing need for the development of robust indices that can encapsulate this multi-dimensional nature of soundscape perception, enabling comparative evaluations and informing targeted interventions to enhance the overall quality of acoustic environments #cite(<Chen2023Developing>);.

== Existing 'Soundscape Indices'
<existing-soundscape-indices>
While the field of soundscape research has witnessed substantial progress, the development of standardized indices for evaluating and comparing soundscapes across diverse contexts has been relatively limited. Existing indices can be broadly seen as arising from two domains: soundscape ecology and soundscape perception.

=== Soundscape Ecology and Bioacoustics
<soundscape-ecology-and-bioacoustics>
Within the realm of soundscape ecology, indices such as the Acoustic Diversity Index \(ADI) and Frequency-dependenty Acoustic Diversity Index \(FADI) #cite(<Xu2023frequency>) have been developed to quantify the diversity and complexity of acoustic signals within a given soundscape. Similar indices \(e.g.~ADI, NDSI, ACI) have also been developed to analyse the acoustic signal of complex acoustic environments and indicate the richness and diversity of biophonic \(natural) and anthrophonic \(human-made) sound sources. However, while these indices contribute valuable insights into the ecological aspects of soundscapes, they do not directly address the perceptual dimensions that are central to the soundscape approach #cite(<SchulteFortkamp2023Soundscapes>);. The multi-dimensional nature of soundscape perception, encompassing factors such as pleasantness, eventfulness, and familiarity, necessitates a more comprehensive and context-sensitive approach.

=== Soundscape Perception
<soundscape-perception>
In the domain of soundscape perception, the Green Soundscape Index \(GSI) #cite(<Kogan2018Green>) has emerged as a notable attempt to quantify the perceived quality of soundscapes, particularly in urban environments. This index incorporates factors such as the presence and levels of natural sounds, human-made sounds, and their respective contributions to the overall soundscape perception.

The GSI is the ratio of the perceived extent of natural sounds \(PNS) to the perceived extent of traffic noise \(PTN):

$ G S I = frac(< P N S >, < P T N >) $

The GSI is noted to range between 1/5 and 5, with several ranges of values given which correspond to general categories of the perceived dominance of traffic noise.

While GSI represents a commendable effort to bridge the gap between objective measurements and subjective perceptions, it remains limited in its ability to capture the full complexity of soundscape perception across diverse contexts. The intricate interplay between various sound sources, their temporal patterns, and the specific context in which they are experienced necessitates a more flexible and adaptable approach to index development.

The Soundscape Perception Index framework presented in this paper differs from these existing indices in two key ways. Firstly, it is not an analysis of an acoustic signal but rather is an index of perception based on soundscape descriptors. Secondly, it does not represent a single target in a particular context, but is a generalisable, extensible, and adaptable framework for scoring soundscapes against any goal defined by the user. The remainder of the paper will introduce and demonstrate this framework, providing a case study of defining an appropriate target.

= Methodology
<methodology>
The index framework, 'the Soundscape Perception Indices \(SPI)' introduced in this paper is defined here as the agreement between an observed or modelled soundscape perception distribution and a target soundscape perception distribution. Its goal is to determine whether a soundscape - whether it be a real-world location, a proposed design, or a hypothetical scenario - aligns with the desired perception of that soundscape. This is achieved by first defining the target distribution, which could represent what is considered to be the 'ideal' soundscape perception for a given context or application. The test distribution is then compared to the target distribution using a distance metric, which quantifies the deviation between the two distributions. The resulting distance value serves as the basis for calculating the SPI, with smaller distances indicating a closer alignment between the perceived soundscape and the target soundscape perception.

We refer to this as an index framework rather than a single index, as the SPI can be tailored to specific contexts and applications by defining a range of target distributions. A single index is thus created for each target distribution. An SPI value therefore does not represent a 'good' or 'bad' soundscape, but rather a measure of how closely the perceived soundscape aligns with the desired target soundscape perception. This approach allows for the development of bespoke indices tailored to specific design goals and objectives, while also enabling cross-comparisons and benchmarking against empirically-defined soundscape archetypes.

There are four steps involved in calculating the SPI, as shown in @fig-bespoke-spi:

+ Define and parameterise the target distribution;
+ Sample the target distribution and prepare test distribution;
+ Compare test and target distribution using the KS distance;
+ Calculate $S P I = 100 \* (1 - K S)$.

#figure([
#box(width: 80%,image("SPI-steps2.png"))
], caption: figure.caption(
position: bottom, 
[
Steps for calculating the SPI.
]), 
kind: "quarto-float-fig", 
supplement: "Figure", 
numbering: "1", 
)
<fig-bespoke-spi>


Throughout this paper, we use the data contained in the International Soundscape Database \(ISD) \(Mitchell et al., 2021a), which includes 1300+ individual responses collected across 13 locations in London and Venice, according to the SSID Protocol #cite(<Mitchell2020Soundscape>);.

== Soundscape Circumplex Distribution
<sec-circumplex-distribution>
SPI is grounded in the soundscape circumplex model #cite(<Axelsson2010principal>);#cite(<Axelsson2012Swedish>);, a robust theoretical foundation for understanding and representing the multi-dimensional nature of soundscape perception. The reason for grounding the SPI in the soundscape circumplex is that we have observed this model \(and its corresponding PAQs) to become the most prevalent assessment model in soundscape literature #cite(<Aletta2023Adoption>);.

Method A is built on a series of descriptors referred to as the Perceived Affective Quality \(PAQ), proposed by #cite(<Axelsson2010principal>);. These PAQs are based on the pleasantness-activity paradigm present in research on emotions and environmental psychology, in particular Russell’s circumplex model of affect #cite(<Russell1980circumplex>);. As summarised by Axelsson: "Russell’s model identifies two dimensions related to the perceived pleasantness of environments and how activating or arousing the environment is."

One benefit of the circumplex model is that, as a whole, it encapsulates several of the other proposed soundscape descriptors - in particular, annoyance, pleasantness, tranquility, and possibly restorativeness #cite(<Aletta2016Soundscape>);. According to #cite(<Axelsson2015How>);, the two-dimensional circumplex model of perceived affective quality provides the most comprehensive information for soundscape assessment. It is also possible that the overall soundscape quality could itself be derived from the pleasant-eventful scores derived for a soundscape. The circumplex also lends itself well to questionnaire-based methods of data collection, as proposed in #cite(<ISO12913Part2>);. In contrast to methods such as soundwalks, interviews, and lab experiments, in-situ questionnaires are able to provide the quality and amount of data which is necessary for statistical modelling. Combined, these factors make the circumplex most appropriate for a single index as it provides a comprehensive summary of soundscape perception.

To move the 8-item PAQ responses into the 2-dimensional circumplex space, we use the projection method first presented in ISO 12913-3:2018. This projection method and its associated formulae were recently updated further in #cite(<Mitchell2023Testing>) to include a correction for the language in which the survey was conducted. #cite(<Mitchell2023Testing>) also provides adjusted angles for translations of the circumplex attributes to be used in calculating the $P_(I S O)$ and $E_(I S O)$ coordinates.

Once the individual perceptual responses are projected into the circumplex space, the resulting data for each location is treated as a circumplex distribution. The circumplex is defined by two axes: $P_(I S O)$ and $E_(I S O)$, which are limited to the range $[- 1 , + 1]$. Typically, data in the soundscape circumplex is treated as a combination of two independent normal distributions, one for each axis #cite(<Mitchell2022How>);#cite(<Ooi2022Probably>);. In some applications, this approach is sufficient for capturing the distribution of soundscape perception, however the method for calculating the SPI requires a more precise approach. The independent normal distribution approach relies on three key assumptions:

+ The two axes are normally distributed.
+ The two axes are independent of each other.
+ The two axes are symmetrically distributed.

While the first assumption is generally valid, the second and third assumptions are not always met in practice. In particular, the distribution of soundscape perception responses in the circumplex is often characterised by a high degree of skewness, which can lead to inaccuracies in the calculation of the SPI. Soundscape circumplex distributions are most appropriately described as a bivariate skew-normal distribution #cite(<Azzalini2005Skew>) which accurately reflects the relationship between the two dimensions of the circumplex and the fact that real-world perceptual distributions have been consistently observed to not be strictly symmetric.

The skew-normal distribution is defined by three parameters: location \($mu$), scale \($sigma$), and shape \($alpha$). The location parameter defines the centre of the distribution, the scale parameter defines the spread of the distribution and the shape parameter defines the skew of the distribution. The one-dimensional skew-normal distribution is defined as #cite(<Azzalini1996Multivariate>);:

$ phi.alt (z ; alpha) = 2 phi.alt (z) Phi (alpha z) quad upright("for") quad z in bb(R) $

where $phi.alt$ and $Phi$ are the standard normal probability density function and distribution function, respectively, and $alpha$ is a shape variable which regulates the skewness. The distribution reduces to a standard normal density when $alpha = 0$. The bivariate skew-normal distribution extends this concept to two dimensions, allowing for the modelling of asymmetric and skewed distributions in a two-dimensional space such as the soundscape circumplex. The multivariate skew-normal \(MSN) distribution including scale and location parameters is given by combining the normal density and distribution functions #cite(<Azzalini1999Statistical>);:

$ Y = 2 phi.alt_k (y - xi ; Omega) Phi { alpha^T omega^(- 1) (y - xi) } $

where $phi.alt_k$ is the #emph[k];-dimensional normal density with location $xi$, shape $alpha$, and covariance matrix $Omega$. $Phi { dot(})$ is the normal distribution function and $alpha$ is a #emph[k];-dimensional shape vector. When $alpha = 0$, $Y$ reduces to the standard multivariate normal $N_k (xi , Omega)$ density. A circumplex distribution can therefore be parameterised with a 2x2 covariance matrix $Omega$, a 2x1 location vector $xi$, and a 2x1 shape vector $alpha$, written as:

$ Y tilde.op M S N (xi , Omega , alpha) $

By fitting an MSN distribution to the soundscape perception responses, it becomes possible to accurately capture the asymmetry and skewness of the distribution. A bivariate skew-normal distribution can be summarised as a set of these three parameters. Once parameterised, the distribution can then be sampled from to generate a synthetic distribution of soundscape perception responses. A demonstration of the results of this process is shown in @fig-dist-example using data from a single location included in the International Soundscape Database \(see #strong[?\@sec-dataset];).

#block[
#block[
#block[
#figure([
#box(width: 864.7272727272727pt, image("index_files/figure-typst/notebooks-SingleIndex-Code-fig-dist-example-output-1.png"))
], caption: figure.caption(
position: bottom, 
[
Example of fitting and sampling from a multivariate skew-normal distribution for data from the Piazza San Marco location.
]), 
kind: "quarto-float-fig", 
supplement: "Figure", 
numbering: "1", 
)
<fig-dist-example>


]
]
]
The parameters for the distribution shown in @fig-dist-example are given by:

$ M S N ([0.065 , 0.679] , mat(delim: "[", 0.149, - 0.064; - 0.064, 0.101) , [0.791 , - 0.767]) $

=== Defining a Target
<defining-a-target>
As introduced in @sec-circumplex-distribution, circumplex data follows a bivariate skew-normal distribution which can be parameterised with a set of direct parameters \(dp). We therefore define a target distribution as a set of these parameters, which can then be used to generate a synthetic distribution of soundscape perception responses.

=== Distance Metric
<distance-metric>
Central to the SPI framework is the concept of a distance metric, which quantifies the deviation of a given soundscape from a desired target soundscape. This distance metric serves as the basis for calculating the SPI value, with smaller distances indicating a closer alignment between the perceived soundscape and the target soundscape perception. The distance between the test and target soundscape distributions is calculated using a two-dimensional Kolmogorov-Smirnov test #cite(<Fasano1987multidimensional>);.

Essentially, we approach this as a problem of \(dis)similarity between soundscapes. The distance metric is then proposed to assess how similar two any given soundscapes distributions are within the circumplex. Taken to the extreme, two perfectly matching distributions in the soundscape circumplex would return a 100% SPI value, while two completely dissimilar distributions would return a 0% SPI value. In practical terms, for the former, this will never be achieved in real world scenarios; for the latter, it is also difficult to estimate how low the SPI value could actually go, and it should be considered that the distance may happen in different directions within the circumplex space. For instance, if a distribution for a vibrant soundscape was taken as a reference, a compared soundscape distribution may exhibit low SPI values for being located in the calm, OR monotonous, OR chaotic regions of the model.

=== Targets
<targets>
The SPI framework introduces two distinct types of targets: bespoke targets and archetypal targets, each serving a unique purpose in the index development process.

==== Bespoke Targets
<bespoke-targets>
Bespoke targets are tailor-made for specific projects, reflecting the desired soundscape perception for a particular application. These targets can be defined by stakeholders, designers, policymakers, or decision-makers based on their unique requirements, objectives, and constraints. This flexibility allows the SPI for a specific project to be tailored to the desire of the stakeholders for how that specific soundscape should function. It can also provide a consistent and quantifiable baseline for scenarios like a soundscape design contest wherein a target is specified and provided to all participants in the contest and the winning proposal is the design with the highest SPI score when assessed against that target.

==== Archetypal Targets
<archetypal-targets>
In contrast to bespoke targets, archetypal targets represent generalized, widely recognized soundscape archetypes which transcend specific applications or projects. These archetypes serve as reference points and enable comparisons across different domains and use cases. #strong[#emph[By providing a framework for these archetypes to be defined, they can be…];]

Additionally, archetypal SPIs can be composed of multiple targets.

=== Data Source
<data-source>
The SPI framework is designed to accommodate a wide range of data sources, including both objective measurements and subjective evaluations. This flexibility enables the framework to be applied to diverse contexts and applications, ranging from urban soundscapes to natural environments, public spaces, and indoor settings.

== Deriving a target
<deriving-a-target>
= Discussion
<discussion>
Although it is expected that the target distribution would usually represent the ideal or goal soundscape perception, it is also possible to define target distributions that represent undesirable or suboptimal soundscape perceptions. For instance, in a soundscape mapping context, it may be beneficial to map and identify chaotic soundscapes across a city in order to better target areas for soundscape interventions. In this case, the target distribution would be set in the chaotic quadrant and a higher SPI would indicate a closer alignment with the target distribution. This flexibility allows the SPI to be applied to a wide range of contexts and applications, enabling the quantification and comparison of soundscape quality across diverse scenarios.

#bibliography("FellowshipRefs-biblatex.bib")

