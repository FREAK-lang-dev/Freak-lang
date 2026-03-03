#include "freak_runtime.h"
#include <string.h>

/* --- Shape definitions --- */
typedef struct {
    freak_word name;
    int64_t power;
    freak_word callsign;
    freak_word status;
} Eishi;

typedef struct {
    freak_word model;
    freak_word variant;
    freak_word weapon;
    freak_word os_ver;
} TSF;


/* --- Forward declarations --- */
static freak_word freak_tier_name(int64_t tier);
static int64_t freak_required_power(int64_t tier);
static freak_word freak_tier_threat(int64_t tier);
static void freak_cosmo_strike(freak_word target, int64_t power);
static void freak_yuuko_analyze(freak_word subject);
static void freak_yuuko_log(freak_word msg);
void Eishi_introduce(Eishi* self);
void Eishi_power_up(Eishi* self, int64_t amount);
void TSF_display(TSF* self);

/* --- Function definitions --- */
static freak_word freak_tier_name(int64_t tier) {
    switch (tier) {
        case ((int64_t)1): {
            return freak_word_lit("Soldier");
            break;
        }
        case ((int64_t)2): {
            return freak_word_lit("Grappler");
            break;
        }
        case ((int64_t)3): {
            return freak_word_lit("Destroyer");
            break;
        }
        case ((int64_t)4): {
            return freak_word_lit("Tank");
            break;
        }
        case ((int64_t)5): {
            return freak_word_lit("Laser");
            break;
        }
        case ((int64_t)6): {
            return freak_word_lit("Fort");
            break;
        }
        case ((int64_t)7): {
            return freak_word_lit("BRAIN");
            break;
        }
    }
    return freak_word_lit("Unknown");
}

static int64_t freak_required_power(int64_t tier) {
    switch (tier) {
        case ((int64_t)1): {
            return ((int64_t)10);
            break;
        }
        case ((int64_t)2): {
            return ((int64_t)25);
            break;
        }
        case ((int64_t)3): {
            return ((int64_t)50);
            break;
        }
        case ((int64_t)4): {
            return ((int64_t)100);
            break;
        }
        case ((int64_t)5): {
            return ((int64_t)200);
            break;
        }
        case ((int64_t)6): {
            return ((int64_t)500);
            break;
        }
        case ((int64_t)7): {
            return ((int64_t)9999);
            break;
        }
    }
    return ((int64_t)0);
}

static freak_word freak_tier_threat(int64_t tier) {
    if ((tier >= ((int64_t)7))) {
        return freak_word_lit("EXTINCTION");
    }
    if ((tier >= ((int64_t)5))) {
        return freak_word_lit("CRITICAL");
    }
    if ((tier >= ((int64_t)3))) {
        return freak_word_lit("HIGH");
    }
    return freak_word_lit("MODERATE");
}

static void freak_cosmo_strike(freak_word target, int64_t power) {
    freak_say(freak_word_lit("=== COSMO ORBITAL STRIKE ==="));
    freak_say(freak_interpolate("Target: %s", freak_word_to_cstr(target)));
    freak_say(freak_interpolate("Yield: %lld terajoules", (long long)power));
    freak_say(freak_word_lit("Status: CONFIRMED — Firing in 3... 2... 1..."));
    freak_say(freak_word_lit(">>> IMPACT <<<"));
    freak_say(freak_word_lit(""));
}

static void freak_yuuko_analyze(freak_word subject) {
    freak_say(freak_interpolate("[YuukoLab] Analyzing: %s...", freak_word_to_cstr(subject)));
    freak_say(freak_word_lit("[YuukoLab] Analysis complete. Results classified."));
}

static void freak_yuuko_log(freak_word msg) {
    freak_say(freak_interpolate("[YuukoLab] %s", freak_word_to_cstr(msg)));
}

void Eishi_introduce(Eishi* self) {
    freak_say(freak_interpolate("%s (%s) — Power: %lld, Status: %s", freak_word_to_cstr(self->callsign), freak_word_to_cstr(self->name), (long long)(self->power), freak_word_to_cstr(self->status)));
}

void Eishi_power_up(Eishi* self, int64_t amount) {
    self->power = (self->power + amount);
}

void TSF_display(TSF* self) {
    freak_say(freak_interpolate("TSF: %s [%s] | Weapon: %s | OS: %s", freak_word_to_cstr(self->model), freak_word_to_cstr(self->variant), freak_word_to_cstr(self->weapon), freak_word_to_cstr(self->os_ver)));
}


int freak_main(void) {
    freak_say(freak_word_lit("============================================"));
    freak_say(freak_word_lit(" BETA EARLY WARNING SYSTEM v1.0"));
    freak_say(freak_word_lit(" Powered by FREAK + muvluv"));
    freak_say(freak_word_lit("============================================"));
    freak_say(freak_word_lit(""));
    /* @protagonist */
    Eishi takeru = (Eishi){ .name = freak_word_lit("Takeru Shirogane"), .power = ((int64_t)9001), .callsign = freak_word_lit("Valkyrie-1"), .status = freak_word_lit("active") };
    Eishi meiya = (Eishi){ .name = freak_word_lit("Meiya Mitsurugi"), .power = ((int64_t)8500), .callsign = freak_word_lit("Valkyrie-2"), .status = freak_word_lit("active") };
    /* @side_character */
    Eishi hayase = (Eishi){ .name = freak_word_lit("Mitsuki Hayase"), .power = ((int64_t)7200), .callsign = freak_word_lit("Storm-1"), .status = freak_word_lit("active") };
    TSF shiranui = (TSF){ .model = freak_word_lit("Type-94 Shiranui"), .variant = freak_word_lit("2nd Phase"), .weapon = freak_word_lit("Type-87 Assault Cannon"), .os_ver = freak_word_lit("XM3") };
    TSF takemikazuchi = (TSF){ .model = freak_word_lit("Type-00 Takemikazuchi"), .variant = freak_word_lit("Type-F"), .weapon = freak_word_lit("Type-74 PB Blade"), .os_ver = freak_word_lit("XM3") };
    freak_say(freak_word_lit("-- PILOT ROSTER --"));
    Eishi_introduce(&takeru);
    Eishi_introduce(&meiya);
    Eishi_introduce(&hayase);
    freak_say(freak_word_lit(""));
    freak_say(freak_word_lit("-- TSF HANGAR --"));
    TSF_display(&shiranui);
    TSF_display(&takemikazuchi);
    freak_say(freak_word_lit(""));
    freak_say(freak_word_lit("-- INCOMING BETA WAVE --"));
    int64_t tier = ((int64_t)1);
    for (int64_t __rep_1 = 0; __rep_1 < ((int64_t)7); __rep_1++) {
        freak_word name = freak_tier_name(tier);
        freak_word threat = freak_tier_threat(tier);
        int64_t req = freak_required_power(tier);
        if ((tier >= ((int64_t)7))) {
            freak_say(freak_interpolate("!! ALERT: %s class detected! Threat: %s !!", freak_word_to_cstr(name), freak_word_to_cstr(threat)));
            freak_say(freak_interpolate("!! Required power: %lld — ALL UNITS ENGAGE !!", (long long)req));
        } else {
            freak_say(freak_interpolate("Detected: %s class | Threat: %s | Power needed: %lld", freak_word_to_cstr(name), freak_word_to_cstr(threat), (long long)req));
        }
        tier = (tier + ((int64_t)1));
        if ((tier > ((int64_t)7))) {
            tier = ((int64_t)1);
        }
    }
    freak_say(freak_word_lit(""));
    freak_yuuko_analyze(freak_word_lit("BETA wave composition"));
    freak_yuuko_log(freak_word_lit("Recommending orbital strike on BRAIN-class target"));
    freak_say(freak_word_lit(""));
    freak_cosmo_strike(freak_word_lit("Sector 7-G"), ((int64_t)500));
    freak_say(freak_word_lit("-- MISSION STATUS --"));
    /* @protagonist */
    /* trust me: "for humanity" (honor: .commander) */
    {
        Eishi_power_up(&takeru, ((int64_t)1000));
    }
    freak_say(freak_interpolate("Takeru final power: %lld", (long long)(takeru.power)));
    freak_say(freak_word_lit("Operation Ouka complete. Casualties... classified."));
    freak_say(freak_word_lit(""));
    freak_say(freak_word_lit("============================================"));
    freak_say(freak_word_lit(" BETA EARLY WARNING SYSTEM — OFFLINE"));
    freak_say(freak_word_lit("============================================"));
    return 0;
}

int main(int argc, char** argv) {
    (void)argc; (void)argv;
    return freak_main();
}
