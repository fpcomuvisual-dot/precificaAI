import { motion } from "framer-motion";

const pageVariants = {
    initial: {
        opacity: 0,
        x: 60,
        scale: 0.98,
    },
    animate: {
        opacity: 1,
        x: 0,
        scale: 1,
        transition: {
            duration: 0.35,
            ease: [0.25, 0.46, 0.45, 0.94],
        },
    },
    exit: {
        opacity: 0,
        x: -40,
        scale: 0.98,
        transition: {
            duration: 0.25,
            ease: "easeInQuad",
        },
    },
};

export default function PageTransition({ children }) {
    return (
        <motion.div
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="min-h-screen"
        >
            {children}
        </motion.div>
    );
}
