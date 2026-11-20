"""Long-form prose reused across manuscript drafts, PDFs and slides (all invented)."""

MS_TITLE = ("Native bee richness recovers within a decade of prairie restoration, "
            "but ground-nesting specialists lag")
MS_AUTHORS = "Miriam K. Achterberg, Rafael Quintero, Priya Natarajan, Jonah Feld"

ABSTRACT = (
    "Prairie restoration is widely promoted as pollinator habitat, yet how quickly bee "
    "communities recover is poorly known. We surveyed wild bees with pan traps and "
    "aerial netting on nine restored tallgrass prairies spanning 0-30 years since "
    "seeding and one never-plowed remnant in east-central Illinois from 2016 to 2022 "
    "(20,937 specimens, 28 taxa). Total species richness rose steeply over the first "
    "six to eight years and then levelled off, reaching values statistically "
    "indistinguishable from the remnant after roughly ten years. In contrast, ground-"
    "nesting specialist bees, including oligolectic Andrena and Calliopsis, continued "
    "to accumulate across the full chronosequence, and even the oldest restorations "
    "supported fewer specialists than the remnant. Specialist richness was positively "
    "associated with bare-ground cover at trap stations, suggesting that nesting "
    "substrate, not floral resources, limits their recovery. Management that maintains "
    "bare ground, such as frequent prescribed fire, may accelerate recovery of the "
    "species most dependent on prairie.")

INTRO = [
    "Less than 0.01% of Illinois's original tallgrass prairie remains. Restoration "
    "plantings on former cropland now cover far more area than remnants, and state "
    "guidance increasingly assumes these plantings will support pollinators within a "
    "few years of establishment.",
    "Most evaluations of restored habitat measure bees in the first few years after "
    "seeding. Chronosequences, in which sites of different ages stand in for time, "
    "allow longer trajectories to be estimated, but have rarely included a remnant "
    "reference or distinguished nesting guilds.",
    "We asked (1) how bee richness and abundance change with years since restoration; "
    "(2) whether specialist and ground-nesting bees follow the same trajectory as the "
    "community as a whole; and (3) whether floral resources or nesting substrate better "
    "explain the recovery of specialists.",
]

METHODS = [
    "Study sites. Ten sites in Champaign, Piatt, Vermilion, Douglas, Macon, Coles and "
    "Ford counties were sampled. Nine are restorations seeded between 1992 and 2019 "
    "with local-ecotype mixes; one is a never-plowed remnant on private land whose "
    "location is withheld here at the request of the Illinois Department of Natural "
    "Resources because it supports the federally endangered rusty patched bumble bee.",
    "Bee sampling. At three stations per site we set fifteen 3.25 oz bowls (five each "
    "of fluorescent blue, fluorescent yellow and white) filled with soapy water for "
    "24 hours, four times per season (May-August). Bowls found tipped or flooded were "
    "recorded as zero effort. Netting along a 50 m transect for 20 minutes per "
    "station supplemented pan traps.",
    "Identification. Specimens were pinned and identified to species where possible "
    "using regional keys; 15% were DNA-barcoded (COI) to resolve Lasioglossum and "
    "Melissodes. Vouchers are deposited in the university insect collection.",
    "Analysis. Rarefied richness was modelled with generalised additive mixed models "
    "with a smooth of restoration age, site as a random intercept, and log bowl-days "
    "as an offset. Specialist richness was modelled separately, with and without the "
    "remnant site, and with bare-ground cover and floral density as covariates.",
]

RESULTS = [
    "We collected 20,937 bees representing 28 taxa. Total richness increased sharply "
    "with restoration age (edf = 2.7, p < 0.001), and fitted richness at ten years was "
    "within the 95% interval of the remnant.",
    "Specialist richness increased approximately linearly across the chronosequence "
    "and did not saturate. The two oldest restorations (24-30 years) supported five "
    "specialist taxa against seven at the remnant. Excluding the remnant reduced but "
    "did not remove the effect of age (p = 0.03).",
    "Bare-ground cover explained more variation in specialist richness than floral "
    "density (delta AIC = 6.4). Blue bowls captured the most bees in every year, but "
    "bowl colour did not change the shape of the age response.",
]

DISCUSSION = [
    "Restorations quickly support a diverse, generalist-dominated bee community, "
    "which is good news for pollination services. The slower return of specialists "
    "means that restoration success judged by total richness overstates recovery of "
    "the species most dependent on prairie.",
    "Because ground-nesting specialists responded to bare ground, managers may be able "
    "to accelerate their recovery with frequent prescribed fire or light disturbance. "
    "This recommendation has been shared with the Illinois Pollinator Working Group.",
    "The remnant anchors the upper end of the specialist gradient. Our results should "
    "be confirmed with additional remnants, which are rare and frequently on private land.",
]

RESPONSE_TO_REVIEWERS = [
    ("Reviewer 1.1: The specialist conclusion rests on one remnant.",
     "We agree this is the key limitation. We now present the remnant as a reference "
     "condition, report the specialist model with and without it (new Fig. S4), and "
     "state the dependence explicitly in the Discussion. The age effect remains "
     "significant without the remnant (p = 0.03)."),
    ("Reviewer 2.1: Describe the trapping effort correction.",
     "Added to Methods: tipped and flooded bowls are now coded as zero effort and log "
     "bowl-days enter as an offset. This corrected an error in the original submission."),
    ("Reviewer 2.2: Was floral density controlled for?",
     "Yes; floral density and bare ground now enter as covariates. Bare ground is the "
     "better predictor (delta AIC = 6.4)."),
    ("Reviewer 3.1: Data deposit for listed species.",
     "Specimen data are deposited with Bombus affinis locations generalised to county, "
     "following Illinois DNR guidance. Exact coordinates are held by the state Natural "
     "Heritage Database."),
]

PROPOSAL_SUMMARY = (
    "Overview. Restored prairies are the main tool for rebuilding pollinator habitat in "
    "the Midwest, but we do not know how long bee communities take to recover or which "
    "species are left behind. This project will survey bees for four years across a "
    "30-year chronosequence of restored tallgrass prairies and a remnant reference, "
    "pairing pan traps and netting with DNA barcoding, floral surveys and nesting-"
    "habitat measurements. Intellectual merit: the project will produce the first "
    "multi-year, guild-resolved estimate of bee recovery after restoration and test "
    "whether nesting substrate limits specialist bees. Broader impacts: findings will "
    "be translated into management guidance with Illinois DNR, train two PhD and three "
    "MS students, and engage landowners through on-farm surveys.")

DMP = [
    "Types of data: specimen records (CSV/SQLite), floral and habitat quadrats (CSV), "
    "DNA barcodes (FASTA, BOLD submissions), photographs (JPEG/TIFF), GIS site layers "
    "(GeoJSON/shapefile), analysis code (R, Python).",
    "Standards: Darwin Core for specimen data; FGDC metadata for GIS layers.",
    "Access: data deposited in a public repository within one year of publication. "
    "Locations of federally listed species will be generalised to county; exact "
    "locations will be provided only to the state Natural Heritage Database.",
    "Preservation: university library repository for a minimum of ten years.",
]

PEER_REVIEW_SHE_WROTE = (
    "CONFIDENTIAL REVIEW - Manuscript ECOAPP-2021-1172 (synthetic)\n"
    "Title: 'Urban vacant lots as refugia for cavity-nesting bees'\n\n"
    "Summary: The authors survey 40 vacant lots in a midwestern city with trap nests "
    "and claim lots older than 15 years support more cavity-nesting species.\n\n"
    "Major concerns:\n1. Lot age is confounded with distance to the river corridor; "
    "please include distance as a covariate.\n2. Trap-nest occupancy was scored once, "
    "in October, so early-season species are missed.\n3. The unpublished data from "
    "the Gregson lab cited in Table 2 cannot be evaluated.\n\n"
    "Recommendation: major revision.\nReviewer: M. Achterberg\n")
